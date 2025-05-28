# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

m = BaselineModel.new

# make a 1 story, 100m X 50m, 1 zone core/perimeter building
m.add_geometry({ 'length' => 100,
                 'width' => 50,
                 'num_floors' => 1,
                 'floor_to_floor_height' => 4,
                 'plenum_height' => 1,
                 'perimeter_zone_depth' => 0 })

# add windows at a 40% window-to-wall ratio
m.add_windows({ 'wwr' => 0.4,
                'offset' => 1,
                'application_type' => 'Above Floor' })

# add thermostats
m.add_thermostats({ 'heating_setpoint' => 24,
                    'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
m.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
m.set_space_type

# add design days to the model (Chicago)
m.add_design_days

# add ASHRAE System type 07, VAV w/ Reheat
m.add_hvac({ 'ashrae_sys_num' => '07' })

# In order to produce more consistent results between different runs,
# we sort the zones by names (only one here anyways...)
zones = m.getThermalZones.sort_by { |z| z.name.to_s }

# CoilSystemCoolingWaterHeatExchangerAssisted
zone = zones[0]
airloop = zone.airLoopHVAC.get
airloop.setName('AirLoopHVAC CoilSystemWaterHX')

# create a CoilSystem object, that creates both a Water Coil and a HX
coil_system = OpenStudio::Model::CoilSystemCoolingWaterHeatExchangerAssisted.new(m)
coil_system.setName('CoilSystemWaterHX')

# Replace the default CoilCoolingWater with CoilSystem, then remove the default one
# Note: it's probably going to end up badly controlled when you place the
# CoilSystem directly on the AirLoopHVAC path and not inside another component
# (such as UnitarySys, cf: https://github.com/NREL/EnergyPlus/issues/7222)
water_coil = coil_system.coolingCoil.to_CoilCoolingWater.get
water_coil.setName('CoilSystemWaterHX CoolingCoil')

coil = airloop.supplyComponents(OpenStudio::Model::CoilCoolingWater.iddObjectType).first.to_CoilCoolingWater.get
# Note that we connect the CoilSystem, NOT the underlying CoilCoolingWater
coil_system.addToNode(coil.airOutletModelObject.get.to_Node.get)
plant = coil.plantLoop.get
# But we have to connect the water_coil itself...
plant.addDemandBranchForComponent(water_coil)
coil.remove

hx = coil_system.heatExchanger.to_HeatExchangerAirToAirSensibleAndLatent.get
hx.setName('CoilSystemWaterHX HX')
if Gem::Version.new(OpenStudio.openStudioVersion) >= Gem::Version.new('3.8.0')
  hx.assignHistoricalEffectivenessCurves
end

# Rename some nodes and such, for ease of debugging
airloop.supplyInletNode.setName("#{airloop.name} Supply Inlet Node")
airloop.supplyOutletNode.setName("#{airloop.name} Supply Outlet Node")
airloop.mixedAirNode.get.setName("#{airloop.name} Mixed Air Node")
coil_system.outletModelObject.get.to_Node.get.setName("#{airloop.name} HX Outlet to Heating Coil Inlet Node")

water_coil.waterInletModelObject.get.setName("#{water_coil.name} Water Inlet Node")
water_coil.waterOutletModelObject.get.setName("#{water_coil.name} Water Outlet Node")
water_coil.controllerWaterCoil.get.setName("#{water_coil.name} Controller")

heating_coil = airloop.supplyComponents(OpenStudio::Model::CoilHeatingWater.iddObjectType).first.to_CoilHeatingWater.get
heating_coil.waterInletModelObject.get.setName("#{airloop.name} Heating Coil Water Inlet Node")
heating_coil.waterOutletModelObject.get.setName("#{airloop.name} Heating Coil Water Outlet Node")
heating_coil.controllerWaterCoil.get.setName("#{airloop.name} Heating Coil Controller")
heating_coil.airOutletModelObject.get.setName("#{airloop.name} Heating Coil Air Outlet to Fan Inlet Node")

# save the OpenStudio model (.osm)
m.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                        'osm_name' => 'in.osm' })
