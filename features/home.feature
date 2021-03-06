Feature: verify the Home page works according to the test acceptance criteria
As a first time visitor to the CKAN page
I want to navigate the home page
So that I can find the information I'm looking for

Background:
   Given I navigate to the CKAN Home page

@smoke @home_page
Scenario: Testing home page
  Then I should see "Welcome -" displayed in the page title

@search @home_page
Scenario: Search in the homepage
  When I enter "qu" in the "Search data" field
  	And I click the search data button
  Then I should see "Datasets - " displayed in the page title

@search @home_page
Scenario: Site Search in the homepage
  When I enter "qu" in the "Site Search data" field
  	And I click the site search data button
  Then I should see "Datasets - " displayed in the page title
