# frozen_string_literal: true

require 'openstudio' unless defined?(OpenStudio)

# The config and helpers are inside this file
require_relative 'test_helpers'

# the tests
class SqlTests < Minitest::Test
  parallelize_me!

  def test_sql_default_fullyear
    # Full year, calendar year not specified
    options = {
      start: nil,
      end: nil,
      isLeapYear: false,
      type: 'Full'
    }
    result = sql_test(options)
  end

  def test_sql_specific_fullyear_nonleap
    # Full year, calendar year hard assigned to a non-leap year
    options = {
      start: '2013-01-01',
      end: '2013-12-31',
      isLeapYear: false,
      type: 'Full'
    }
    result = sql_test(options)
  end

  def test_sql_specific_fullyear_leap
    # Full year, calendar year hard assigned to a leap year
    options = {
      start: '2012-01-01',
      end: '2012-12-31',
      isLeapYear: true,
      type: 'Full'
    }
    result = sql_test(options)
  end

  def test_sql_partial_leap_mid
    # Partial with leap day in middle
    options = {
      start: '2012-02-10',
      end: '2012-03-10',
      isLeapYear: true,
      type: 'Partial'
    }
    result = sql_test(options)
  end

  def test_sql_partial_leap_end
    # Partial with leap day at end
    options = {
      start: '2012-02-01',
      end: '2012-02-29',
      isLeapYear: true,
      type: 'Partial'
    }
    result = sql_test(options)
  end

  def test_sql_partial_leap_start
    # Partial with leap day at start
    options = {
      start: '2012-02-29',
      end: '2012-03-10',
      isLeapYear: true,
      type: 'Partial'
    }
    result = sql_test(options)
  end

  def test_sql_wrap_nonleap
    # Wrap-around with no leap days
    options = {
      start: '2013-02-10',
      end: '2014-02-09',
      isLeapYear: false,
      type: 'Wrap-around'
    }
    result = sql_test(options)
  end

  def test_sql_wrap_leap
    # Wrap-around with leap day
    options = {
      start: '2012-02-10',
      end: '2013-02-09',
      isLeapYear: true,
      type: 'Wrap-around'
    }
    result = sql_test(options)
  end
end
