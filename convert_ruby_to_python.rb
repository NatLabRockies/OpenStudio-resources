# frozen_string_literal: true

require 'optparse'
require 'pathname'
require 'parser/current'
require 'rubocop-ast'
require 'rubocop'

# opt-in to most recent AST format:
Parser::Builders::Default.emit_lambda = true

NAMESPACE_REPLACEMENTS = {
  Airflow: 'airflow',
  EnergyPlus: 'energyplus',
  EPJSON: 'epjson',
  GbXML: 'gbxml',
  Gltf: 'gltf',
  ISOModel: 'isomodel',
  Measure: 'measure',
  Model: 'model',
  OSVersion: 'osversion',
  Radiance: 'radiance',
  SDD: 'sdd'
}.freeze

class Rule < Parser::AST::Processor
  include RuboCop::AST::Traversal

  def initialize(rewriter)
    @rewriter = rewriter
  end

  def create_range(begin_pos, end_pos)
    Parser::Source::Range.new(@rewriter.source_buffer, begin_pos, end_pos)
  end
end

class ReplaceRequire < Rule
  def on_send(node)
    if node.method_name == :require
      raise if node.child_nodes.size != 1

      req = node.child_nodes[0]
      raise if !req.str_type?

      @rewriter.replace(node.loc.expression, "import #{req.value}")
    elsif node.method_name == :require_relative
      raise if node.child_nodes.size != 1

      req = node.child_nodes[0]
      raise if !req.str_type?

      if req.value == 'lib/baseline_model'
        @rewriter.replace(node.loc.expression, 'from lib.baseline_model import BaselineModel')
      else
        # raise if req.value != "lib/baseline_model"
        puts "Unknown #{req.value}"
      end
    end
  end
end

class ArrayFirst < Rule
  def on_send(node)
    return unless node.method_name == :first

    range = create_range(node.loc.dot.begin_pos, node.loc.expression.end_pos)
    @rewriter.replace(range, '[0]')
  end
end

class AddParenthesesToMethods < Rule
  def on_send(node)
    return unless node.arguments.empty? && !node.loc.expression.source_line.end_with?('()')

    range = create_range(node.loc.expression.end_pos, node.loc.expression.end_pos)
    @rewriter.replace(range, '()')
    # puts node.receiver
  end
end

class ProcessHash < Rule
  def on_hash(node)
    # @rewriter.replace(node.loc.expression, node.loc.expression.source.gsub('=>',':'))

    args = []
    node.child_nodes.each do |pair_node|
      raise if !pair_node.pair_type?
      raise if pair_node.child_nodes.size != 2
      raise if !pair_node.child_nodes[0].str_type?

      args << "#{pair_node.child_nodes[0].value}=#{pair_node.child_nodes[1].loc.expression.source}"
    end
    @rewriter.replace(node.loc.expression, args.join(', '))
  end
end

class SyntaxBreakingReplacements < Rule
  def on_begin(node)
    return
  end

  def on_const(node)
    replace_const_namespaces(node)
  end

  def on_true(node)
    @rewriter.replace(node.loc.expression, 'True')
  end

  def on_false(node)
    @rewriter.replace(node.loc.expression, 'False')
  end

  def on_block(node)
    replace_sort_bys(node)
    replace_each(node)
    replace_each_with_index(node)
  end

  def on_if(node)
    # DISABLED, it breaks if you have more than two ifs
    # return

    return if node.nil?
    return if node.unless? || node.ternary? # || node.modifier_form?

    @rewriter.insert_after(node.condition.loc.expression, ':')
    if node.loc.end
      # Remove last end
      @rewriter.replace(node.loc.end, '')
    end
    if node.else_branch && !node.else_branch.if_type? && node.else?
      @rewriter.insert_after(node.else?, ':')
    end
    return unless node.keyword == 'elsif'

    @rewriter.replace(node.loc.keyword, 'elif')
  end

  def on_send(node)
    replace_puts(node)
    replace_new(node)
    replace_append(node)
    process_raise_if(node)
    replace_select(node)
    replace_each_block_pass(node)
    replace_not_operator(node)
  end

  def on_next(node)
    return unless node.parent.modifier_form?

    rewritten = "#{node.parent.keyword} #{node.parent.condition.source}: continue"
    @rewriter.replace(node.parent.loc.expression, rewritten)
  end

  def process_raise_if(node)
    return unless node.send_type?
    return unless node.method_name == :raise
    return unless node.parent.modifier_form?

    args = node.arguments? ? "(#{node.arguments.map(&:source).join(', ')})" : ''

    rewritten = "#{node.parent.keyword} #{node.parent.condition.source}: raise ValueError#{args}"
    @rewriter.replace(node.parent.loc.expression, rewritten)
  end

  def replace_sort_bys(node)
    # Definitely breaking the Ruby syntax
    return unless node.method_name == :sort_by

    receiver = node.receiver
    body = node.body

    return unless receiver && body

    body_str = node.body.source
    args_str = node.arguments.child_nodes.map(&:source).join(', ')

    # Build the corrected code
    corrected_code = "sorted(#{receiver.source}, key=lambda #{args_str}: #{body_str})"

    # Replace the original code with the corrected one
    range = create_range(node.loc.expression.begin_pos, node.loc.expression.end_pos)
    @rewriter.replace(range, corrected_code)
  end

  def replace_each_with_index(node)
    return unless node.method_name == :each_with_index

    corrected_code = "for #{node.arguments.reverse.map(&:source).join(', ')} in enumerate(#{node.receiver.source}):"
    range = create_range(node.loc.expression.begin_pos, node.arguments.loc.expression.end_pos)
    @rewriter.replace(range, corrected_code)
    @rewriter.replace(node.loc.end, '') # Remove end
  end

  def replace_each(node)
    return unless node.method_name == :each

    corrected_code = "for #{node.arguments.map(&:source).join(', ')} in #{node.receiver.source}:"
    range = create_range(node.loc.expression.begin_pos, node.arguments.loc.expression.end_pos)
    @rewriter.replace(range, corrected_code)
    @rewriter.replace(node.loc.end, '') # Remove end
  end

  def replace_puts(node)
    return unless node.method_name == :puts

    print_content = node.arguments.map(&:source).join(', ')
    f_string = print_content.include?('#{') ? 'f' : ''
    print_content.gsub!('#{', '{')

    corrected_code = "print(#{f_string}#{print_content})"

    @rewriter.replace(node.loc.expression, corrected_code)
  end

  def replace_new(node)
    return unless node.method_name == :new

    range = create_range(node.loc.dot.begin_pos, node.loc.selector.end_pos)
    @rewriter.replace(range, '')
  end

  def replace_append(node)
    return unless node.method_name == :<< && node.receiver&.lvar_type?

    corrected_code = "#{node.receiver.source}.append(#{node.arguments.map(&:source).join(', ')})"
    @rewriter.replace(node.loc.expression, corrected_code)
  end

  def replace_each_block_pass(node)
    return unless node.method_name == :each || node.method_name == :map
    return if node.block_type?
    return if node.block_node
    return unless node.arguments.one? && node.first_argument.block_pass_type?

    block_pass = node.first_argument
    return unless block_pass.children.first&.sym_type?

    @rewriter.replace(node.loc.expression, "[x.#{block_pass.children.first.value}() for x in #{node.receiver.source}]")
  end

  def replace_select(node)
    return unless node.method_name == :select
    return if node.block_type?
    return unless node.block_node

    args = node.block_node.arguments.map(&:source).join(', ')
    list_comprehension = "[#{args} for #{args} in  #{node.receiver.source} if #{node.block_node.body.source}]"
    @rewriter.replace(node.loc.expression, list_comprehension)
  end

  def replace_not_operator(node)
    return unless node.method_name == :!

    @rewriter.replace(node.loc.selector, 'not ')
  end

  def replace_const_namespaces(node)
    # This is **that** breaking but still...
    if !node.parent&.const_type?
      return unless node.namespace&.short_name == :OpenStudio || node.namespace&.namespace&.short_name == :OpenStudio

      @rewriter.replace(node.loc.double_colon, '.')
      return
    end
    # puts "node=#{node}"
    if !node.namespace
      return unless node.short_name == :OpenStudio

      @rewriter.replace(node.loc.expression, 'openstudio')
      return
    end

    puts "node.namespace.short_name=#{node.namespace.short_name}"
    return unless node.namespace.short_name == :OpenStudio
    raise "#{node.short_name} not found" if !NAMESPACE_REPLACEMENTS.include?(node.short_name)

    # Replace Model with model
    range = create_range(node.loc.double_colon.begin_pos, node.loc.name.end_pos)
    @rewriter.replace(range, ".#{NAMESPACE_REPLACEMENTS[node.short_name]}")
  end
end

class ReplaceCaseWithIf < Rule
  def on_case(node)
    return unless node.conditional?

    condition = node.condition.source
    is_first = true
    when_branches = node.when_branches.map do |when_node|
      content = process_when_branch(when_node, is_first)
      is_first = false
      content
    end
    else_branch = process_else_branch(node.else_branch)

    # Build the corrected code
    corrected_code = <<~RUBY
      #{when_branches.join("\n")}
      #{else_branch}
      end
    RUBY

    # Replace the original code with the corrected one
    range = create_range(node.loc.keyword.begin_pos, node.loc.end.end_pos)
    @rewriter.replace(range, corrected_code)
  end

  private

  def process_when_branch(when_node, is_first)
    condition = when_node.conditions.map { |cond| "#{when_node.parent.condition.source} == #{cond.source}" }.join(' || ')
    body = when_node.body.source
    keyword = is_first ? 'if' : 'elsif'
    <<~RUBY
      #{keyword} #{condition}
        #{body}
    RUBY
  end

  def process_else_branch(else_branch)
    return '' unless else_branch

    "else\n#{else_branch.source}"
  end
end

# Main method.

def replace_gem_version(code)
  return code.gsub('Gem::Version', 'openstudio.VersionString').gsub('OpenStudio.openStudioVersion', 'openstudio.openStudioVersion')
end

def ensure_all_namespaces(code)
  # Some replacements are left out, just force them

  code.gsub!('OpenStudio::', 'openstudio.')
  code.gsub!('OpenStudio.', 'openstudio.')
  NAMESPACE_REPLACEMENTS.each do |ruby_sym, replacement|
    code.gsub!("#{ruby_sym}::", "#{replacement}::")
  end
  code.gsub!('Baselinemodel', 'BaselineModel')
  code.gsub!('::', '.')
  code.gsub!('.new(', '(')
  code.gsub!('elsif ', 'elif ')
  return code
end

def break_if_continue(code)
  return code.split("\n", -1).map do |line|
    if line.strip.start_with?('if') && line.strip.end_with?(': continue')
      leading_spaces = line.length - line.lstrip.length
      line.gsub(': continue', ":\n#{' ' * (leading_spaces + 4)}continue")
    elsif (line.strip.start_with?('if') || line.strip.start_with?('elif') || line.strip.start_with?('else')) && line.strip[-1] != ':'
      line += ':'
    else
      line
    end
  end.join("\n")
end

def replace_not_operator(code)
  return code.gsub('if !', 'if not ')
end

def post_cleanup(code)
  code = replace_gem_version(code)
  code = ensure_all_namespaces(code)
  code = break_if_continue(code)
  code = replace_not_operator(code)
  code = code.gsub('&&', 'and')
  code = code.gsub('||', 'or')
  code = code.gsub('.nil?', 'is None')
  code = code.gsub(' nil', ' None')
  return code
end

def process_file(file)
  return unless File.exist?(file)

  code = File.read(file)
  return process_code(code)
end

def align_4_spaces(code)
  config_path = 'temp_config.yml'
  File.write(config_path, 'Layout/IndentationWidth:
    Width: 4
  ')
  File.write('temp.rb', code)
  options, paths = RuboCop::Options.new.parse(['-a', '--format=simple', '--only', 'Layout/IndentationWidth,Layout/EndAlignment,Layout/ElseAlignment,Layout/IndentationConsistency',
                                               'temp.rb'])
  store = RuboCop::ConfigStore.new
  store.options_config = config_path
  runner = RuboCop::Runner.new(options, store)
  runner.run(paths)
  reformatted_code = File.read('temp.rb')
  File.delete('temp.rb')
  File.delete('temp_config.yml')
  return reformatted_code
end

def process_code(
  code,
  non_breaking_rule_classes = [ReplaceCaseWithIf, ArrayFirst, AddParenthesesToMethods, ReplaceRequire, ProcessHash],
  breaking_rule_classes = [SyntaxBreakingReplacements]
)
  code.gsub!('.name.to_s', '.nameString')
  code.gsub!('.name.get', '.nameString')

  non_breaking_rule_classes.each do |rule_class|
    puts "Processing #{rule_class}"
    code = process_rule(rule_class, code)
  end
  code = align_4_spaces(code)

  frozen_lit = "# frozen_string_literal: true\n\n"
  if code.start_with?(frozen_lit)
    code = code[frozen_lit.size..]
  end

  breaking_rule_classes.each do |rule_class|
    puts "Processing #{rule_class}"
    code = process_rule(rule_class, code)
  end
  post_cleanup(code)
end

def process_rule(rule_class, code)
  source = RuboCop::AST::ProcessedSource.new(code, 2.7)
  source_buffer = source.buffer
  rewriter = Parser::Source::TreeRewriter.new(source_buffer)
  rule = rule_class.new(rewriter)
  source.ast.each_node { |n| rule.process(n) }
  rewriter.process
end

def reformat_python_file(file_name)
  return system("black -l 120 #{file_name}")
end

def port_file(file_name, verbose: false)
  code = process_file(file_name)

  # code.gsub!('OpenStudio::Model::', 'openstudio.model.')
  code.gsub!('Dir.pwd()', 'None')
  if verbose
    puts '=' * 80
    puts code
  end

  target_file = File.join(File.dirname(file_name), "#{File.basename(file_name, '.rb')}.py")
  puts "target file: #{target_file}"

  File.write(target_file, code)
  valid_syntax = reformat_python_file(target_file)

  return target_file, valid_syntax
end

###############################################################################
#                                    C L I                                    #
###############################################################################

# define the input parameters
options = {}
options[:verbose] = false

OptionParser.new do |opts|
  opts.on('-f', '--file RUBYFILE', 'Ruby file to convert') do |ruby_file|
    options[:ruby_file] = ruby_file
  end

  opts.on('-v', '--verbose', 'Print errors that have been ignored') do |verbose|
    options[:verbose] = verbose
  end
end.parse!

raise '--file is required' if options[:ruby_file].nil?

ruby_file = Pathname.new(options[:ruby_file])
raise "#{ruby_file} does not exist" unless ruby_file.exist?
raise "#{ruby_file} is not a ruby file" unless ruby_file.extname == '.rb'

port_file(ruby_file, verbose: options[:verbose])
