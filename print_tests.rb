# frozen_string_literal: true

n = 0
Dir.glob('model/simulationtests/*.*').each do |f|
  if /\.osm$/.match(f) || /\.rb$/.match(f) || /\.py$/.match(f)
    filename = File.basename(f)
    puts "  def test_#{filename.gsub('.', '_')}"
    puts "    result = sim_test('#{filename}')"
    puts '  end'
    puts
    n += 1
  end
end

puts "Found #{n} tests"
