Feature: verify the Datasets page works according to the test acceptance criteria
As a first time visitor to the CKAN page
I want to search inside the Datasets page
So that I can find the Datasets I'm looking for

Background:
   Given I navigate to the Datasets page


@smoke
Scenario Outline: Search in the datasets page
  When I enter "<search-term>" in the "Search datasets" field
  	And I click the search datasets button
  Then I should see "Datasets - " displayed in the page title

Examples:
   | search-term |
   | qu          |


@search
Scenario Outline: Verify that search term appears in URL query string
  When I enter "<search-term>" in the "Search datasets" field
  	And I click the search datasets button
  Then I should see "q=<search-term>" in the URL query string

Examples:
   | search-term |
   | qu          |

@search
Scenario Outline: Verify that sort order appears in URL query string
  Given I enter "qu" in the "Search datasets" field
  	And I click the search datasets button
  When I select Order By "<sort-order>"
  Then I should see the Order By option set to "<sort-order>"
  	And I should see "sort=<sort-parameter>" in the URL query string

Examples:
   | sort-order      | sort-parameter         |
   | Relevance       | score+desc             |
   | Name Ascending  | title_string+asc       |
   | Name Descending | title_string+desc      |
   | Last Modified   | metadata_modified+desc |
