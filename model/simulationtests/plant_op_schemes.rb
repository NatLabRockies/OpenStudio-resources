# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 2,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 1,
                     'perimeter_zone_depth' => 3 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add ASHRAE System type 07, VAV w/ Reheat
model.add_hvac({ 'ashrae_sys_num' => '07' })

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# manually add op schemes instead of depending on os defaults

chiller = model.getChillerElectricEIRs.first
chilled_plant = chiller.plantLoop.get
chiller2 = OpenStudio::Model::ChillerElectricEIR.new(model)
chilled_plant.addSupplyBranchForComponent(chiller2)
# A default constructed load scheme has a single large load range
cooling_op_scheme = OpenStudio::Model::PlantEquipmentOperationCoolingLoad.new(model)
# This method adds the equipment to the existing load range
cooling_op_scheme.addEquipment(chiller)
cooling_op_scheme.addEquipment(chiller2)
# This cuts the load range into two pieces with only chiller2 operating on the lower end of the range
# See PlantEquipmentOperationRangeBasedScheme for details about this api
lower_range_equipment = []
lower_range_equipment.push(chiller2)
cooling_op_scheme.addLoadRange(25000.0, lower_range_equipment)
chilled_plant.setPlantEquipmentOperationCoolingLoad(cooling_op_scheme)

boiler = model.getBoilerHotWaters.first
heating_plant = boiler.plantLoop.get
boiler2 = OpenStudio::Model::BoilerHotWater.new(model)
heating_plant.addSupplyBranchForComponent(boiler2)

heating_op_scheme = OpenStudio::Model::PlantEquipmentOperationHeatingLoad.new(model)
heating_op_scheme.addEquipment(boiler)
heating_op_scheme.addEquipment(boiler2)
heating_plant.setPlantEquipmentOperationHeatingLoad(heating_op_scheme)

lower_heating_range_equipment = []
lower_heating_range_equipment.push(boiler2)
heating_op_scheme.addLoadRange(25000.0, lower_heating_range_equipment)
heating_plant.setPlantEquipmentOperationHeatingLoad(heating_op_scheme)

tower = model.getCoolingTowerSingleSpeeds.first
cond = tower.plantLoop.get

# NOTE: Prior to E+ 23.1.0 (OS 3.6.0), the PlantEq based on outdoor temperature
# were not working correctly in E+ and the equipment would not turn on
# see https://github.com/NREL/EnergyPlus/pull/9727
tower_scheme = OpenStudio::Model::PlantEquipmentOperationOutdoorWetBulb.new(model)
cond.setPrimaryPlantEquipmentOperationScheme(tower_scheme)
# tower_scheme.addEquipment(tower)
tower_equipment = []
tower_scheme.addLoadRange(-50.0, tower_equipment)
tower_equipment.push(tower)
tower_scheme.addLoadRange(23.0, tower_equipment)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
