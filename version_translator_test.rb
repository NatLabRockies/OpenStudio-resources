# frozen_string_literal: true

require 'openstudio'

OpenStudio::Logger.instance.standardOutLogger.setLogLevel(OpenStudio::Debug)

vt = OpenStudio::OSVersion::VersionTranslator.new
m = vt.loadModel('./model/simulationtests/foundation_kiva.osm')

vt.errors.each { |e| puts e.logMessage }
vt.warnings.each { |w| puts w.logMessage }
# puts m.get
