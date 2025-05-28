Pull request overview
---------------------

<!--- **Please change this line to a description of the pull request, with useful supporting information.** -->

<!---  **Note**: You can open a specific PR template directly by appending `?template=xxx` argument with the value `newtest.md`, `testfix.md` or `newtestforexisting.md`. -->

Link to relevant GitHub Issue(s) if appropriate:

Link to the **Ubuntu 22.04 .deb** installer to use for CI Testing. If not set, it will default to latest official release.
[OpenStudio Installer]: http://


This Pull Request is concerning:

 - [ ] **Case 1 - `NewTest`:** a new test for a new model API class,
 - [ ] **Case 2 - `TestFix`:** a fix for an existing test. The GitHub issue should be referenced in the PR description
 - [ ] **Case 3 - `NewTestForExisting`:** a new test for an already-existing model API class
 - [ ] **Case 4 - `Other`:** Something else, like maintenance of the repo, or just committing test results with a new OpenStudio version.

Depending on your answer, please fill out the required section below, and delete the three others.
Leave the review checklist in place.


----------------------------------------------------------------------------------------------------------

### Case 1: New test for a new model API class

Please include which class(es) you are adding a test to specifically test for.
Include a link to the OpenStudio Pull Request in which you are adding the new classes, or the class itself if already on develop.
<!---
> eg:
>
> This pull request is in relation with the Pull Request [NREL/OpenStudio#3031](https://github.com/NREL/OpenStudio/pull/3031), and  will specifically test for the following classes:
> * `AirTerminalSingleDuctConstantVolumeFourPipeBeam`
> * `CoilCoolingFourPipeBeam`
> * `CoilHeatingFourPipeBeam`
> * Additionally it explicitly tests for the existing class [TableMultiVariableLookUp](https://github.com/NREL/OpenStudio/blob/develop/openstudiocore/src/model/TableMultiVariableLookup.hpp)
-->

#### Work Checklist

The following has been checked to ensure compliance with the guidelines:

 - [ ] Tests pass either:
     - [ ] with official OpenStudio release (include version):
         - [ ] A matching OSM test has been added from the successful run of the Ruby one with the official OpenStudio release
         - [ ] The label `AddedOSM` has been added to this PR
         - [ ] All new `out.osw` have been committed

     - [ ] with current develop (incude SHA):
         - [ ] The label `PendingOSM` has been added to this PR
         - [ ] A matching OSM test has not yet been added because the official release is pending, but `model_tests.rb` has a TODO.
            ```ruby
            def test_airterminal_cooledbeam_rb
              result = sim_test('airterminal_cooledbeam.rb')
            end

            # TODO: To be added in the next official release after: 2.5.0
            # def test_airterminal_fourpipebeam_osm
            #   result = sim_test('airterminal_fourpipebeam.osm')
            # end
            ```
        - [ ] No `out.osw` have been committed as they need to be run with an official OpenStudio version


 - [ ] **Ruby test is stable**: when run multiple times on the same machine, it produces the same total site kBTU.
    Please paste the heatmap png generated after running the following commands:
     - [ ] I ensured that I assign systems/loads/etc in a repeatable manner (eg: if I assign stuff to thermalZones, I do `model.getThermalZones.sort_by{|z| z.name.to_s}.each do ...` so I am sure I put the same ZoneHVAC systems to the same zones regardless of their order)
     - [ ] I tested stability using `process_results.py` (see `python process_results.py --help` for usage).
    Please paste the text output or heatmap png generated after running the following commands:
        ```bash
        # Clean up all custom-tagged OSWs
        python process_results.py test-stability clean
        # Run your test 5 times in a row. Replace `testname_rb` (eg `airterminal_fourpipebeam_rb`)
        python process_results.py test-stability run -n testname_rb
        # Check that they all passed
        python process_results.py test-status --tagged
        # Check site kBTU differences
        python process_results.py heatmap --tagged

        ```

 - [ ] **Object has been added to `autosize_hvac.rb` to ensure the autosizedXXX values methods do work**

----------------------------------------------------------------------------------------------------------

### Case 2: Fix for an existing test

Please include a link to the specific test you are modifying, and a description of the changes you have made and why they are required.

### Work Checklist

**The change:**
 - [ ] affects site kBTU results
 - [ ] does not affect total site kBTU results

**If it affects total site kBTU:**
 - [ ] Test has been run backwards (see [Instructions for Running Docker](https://github.com/NREL/OpenStudio-resources/blob/develop/doc/Instructions_Docker.md)) for all OpenStudio versions to update numbers
 - [ ] Changes did not make the test fail in older OpenStudio versions where it used to pass
 - [ ] Matching OSM has been replaced with the output of the ruby test for the oldest OpenStudio release where it passes.
 - [ ] All new/changed `out.osw` have been committed for official OpenStudio versions only

**Either way:**

 - [ ] **Ruby test is still stable**: when run multiple times on the same machine, it produces the same total site kBTU.
     - [ ] I ensured that I assign systems/loads/etc in a repeatable manner (eg: if I assign Terminals to thermalZones, I do `model.getThermalZones.sort_by{|z| z.name.to_s}.each do ...` so I am sure I put the same ZoneHVAC systems to the same zones regardless of their order)
     - [ ] I tested stability using `process_results.py` (see `python process_results.py --help` for usage).
    Please paste the text output or heatmap png generated after running the following commands:
        ```bash
        # Clean up all custom-tagged OSWs
        python process_results.py test-stability clean
        # Run your test 5 times in a row. Replace `testname_rb` (eg `airterminal_fourpipebeam_rb`)
        python process_results.py test-stability run -n testname_rb
        # Check that they all passed
        python process_results.py test-status --tagged
        # Check site kBTU differences
        python process_results.py heatmap --tagged

        ```

 - [ ] **If relevant, new fields that can be autosized have been added to `autosize_hvac.rb` to ensure the autosizedXXX values methods do work**


----------------------------------------------------------------------------------------------------------

### Case 3: New test for an already-existing model API class

Please include which class(es) you are adding a test to specifically test for as it was currently not being tested for.
Include a link to the OpenStudio model classes themselves.

> eg:
>
> This pull request adds missing tests for the following classes:
> *  [AvailabilibityManagerDifferentialThermostat](https://github.com/NREL/OpenStudio/blob/develop/openstudiocore/src/model/AvailabilityManagerDifferentialThermostat.hpp)
> *  [AvailabilibityManagerHighTemperatureTurnOff](https://github.com/NREL/OpenStudio/blob/develop/openstudiocore/src/model/AvailabilityManagerHighTemperatureTurnOff.hpp)
> *  [AvailabilibityManagerHighTemperatureTurnOn](https://github.com/NREL/OpenStudio/blob/develop/openstudiocore/src/model/AvailabilityManagerHighTemperatureTurnOn.hpp)

#### Work Checklist

The following has been checked to ensure compliance with the guidelines:

 - [ ] **Test has been run backwards** (see [Instructions for Running Docker](https://github.com/NREL/OpenStudio-resources/blob/develop/doc/Instructions_Docker.md)) for all OpenStudio versions
 - [ ] **A Matching OSM test** has been added with the output of the ruby test for the oldest OpenStudio release where it passes (include OpenStudio Version)

 - [ ] **Ruby test is stable** in the last OpenStudio version: when run multiple times on the same machine, it produces the same total site kBTU.
    - [ ] I ensured that I assign systems/loads/etc in a repeatable manner (eg: if I assign stuff to thermalZones, I do `model.getThermalZones.sort_by{|z| z.name.to_s}.each do ...` so I am sure I put the same ZoneHVAC systems to the same zones regardless of their order)
     - [ ] I tested stability using `process_results.py` (see `python process_results.py --help` for usage).
    Please paste the text output or heatmap png generated after running the following commands:
        ```bash
        # Clean up all custom-tagged OSWs
        python process_results.py test-stability clean
        # Run your test 5 times in a row. Replace `testname_rb` (eg `airterminal_fourpipebeam_rb`)
        python process_results.py test-stability run -n testname_rb
        # Check that they all passed
        python process_results.py test-status --tagged
        # Check site kBTU differences
        python process_results.py heatmap --tagged

        ```

 - [ ] **Object has been added to `autosize_hvac.rb` to ensure the autosizedXXX values methods do work**

----------------------------------------------------------------------------------------------------------

### Case 4: Other

Please be as explicit as possible about the changes you have made, and why they are warranted.


----------------------------------------------------------------------------------------------------------

### Review Checklist

 - [ ] Code style (indentation, variable names, strip trailing spaces)
 - [ ] Functional code review (it has to work!)
 - [ ] Matching OSM test has been added or `# TODO` added to `model_tests.rb`
 - [ ] Appropriate `out.osw` have been committed
 - [ ] Test is stable
 - [ ] Object is tested in `autosize_hvac` as appropriate
 - [ ] The appropriate labels have been added to this PR:
   - [ ] One of: `NewTest`, `TestFix`, `NewTestForExisting`, `Other`
   - [ ] If `NewTest`: add `PendingOSM` or `AddedOSM`
