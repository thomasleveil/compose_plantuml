Feature: Link Graph
  As a DevOps
  I want to have readable, formatted docker-compose files
  so that I see errors soon

  Scenario: Requires Version
    Given a file named "compose.yml" with:
      """
      foo:
        image: bar
      """
    When I run `bin/compose_plantuml compose.yml`
    Then it should fail with:
      """
      docker-compose version exception: version not present
      """

  Scenario: Requires Version 2
    Given a file named "compose.yml" with:
      """
      version: 1
      """
    When I run `bin/compose_plantuml compose.yml`
    Then it should fail with exactly:
      """
      docker-compose version exception: need version 2, but got 1

      """

  Scenario: Basic Link Graph
    Given a file named "compose.yml" with:
      """
      version: "2"
      services:
        first:
          links:
            - second
        second: {}
      """
    When I run `bin/compose_plantuml compose.yml`
    Then it should pass with exactly:
      """
      [first]
      [second]
      [first] --> [second]

      """

  Scenario: Ignores Aliases
    Given a file named "compose.yml" with:
      """
      version: "2"
      services:
        first:
          links:
            - second:second_alias
        second: {}
      """
    When I run `bin/compose_plantuml compose.yml`
    Then it should pass with exactly:
      """
      [first]
      [second]
      [first] --> [second]

      """
