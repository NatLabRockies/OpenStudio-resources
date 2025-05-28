class OpenStudio::Model::ChillerElectricEIR
  def maxCoolingCapacity
    if referenceCapacity.is_initialized
      referenceCapacity
    else
      autosizedReferenceCapacity
    end
  end

  def maxAirFlowRate
    if referenceCondenserFluidFlowRate.is_initialized
      referenceCondenserFluidFlowRate
    else
      autosizedReferenceCondenserFluidFlowRate
    end
  end

  def maxWaterFlowRate
    if referenceChilledWaterFlowRate.is_initialized
      referenceChilledWaterFlowRate
    else
      autosizedReferenceChilledWaterFlowRate
    end
  end

  def maxCoolingCapacityAutosized
    if referenceCapacity.is_initialized
      # Not autosized if hard size field value present
      return OpenStudio::OptionalBool.new(false)
    else
      return OpenStudio::OptionalBool.new(true)
    end
  end

  def maxAirFlowRateAutosized
    if referenceCondenserFluidFlowRate.is_initialized
      # Not autosized if hard size field value present
      return OpenStudio::OptionalBool.new(false)
    else
      return OpenStudio::OptionalBool.new(true)
    end
  end

  def maxWaterFlowRateAutosized
    if referenceChilledWaterFlowRate.is_initialized
      # Not autosized if hard size field value present
      return OpenStudio::OptionalBool.new(false)
    else
      return OpenStudio::OptionalBool.new(true)
    end
  end

  def performanceCharacteristics
    effs = []
    effs << [referenceCOP, 'Reference COP']
    # E+ 8.0 changed it to Fraction of Compressor Electric Consumption Rejected by Condenser
    # effs << [compressorMotorEfficiency, 'Compressor Motor Efficiency']
    return effs
  end
end
