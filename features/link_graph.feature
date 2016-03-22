Feature: Link Graph
  As a DevOps,
  I want to get a link graph of my system
  so that I know where the data flows.

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
    When I run `bin/compose_plantuml --link-graph compose.yml`
    Then it should pass with exactly:
      """
      skinparam componentStyle uml2
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
    When I run `bin/compose_plantuml --link-graph compose.yml`
    Then it should pass with exactly:
      """
      skinparam componentStyle uml2
      [first]
      [second]
      [first] --> [second]

      """

  Scenario: Supports Dependencies
    Given a file named "compose.yml" with:
      """
      version: "2"
      services:
        first:
          depends_on:
            - second
        second: {}
      """
    When I run `bin/compose_plantuml --link-graph compose.yml`
    Then it should pass with exactly:
      """
      skinparam componentStyle uml2
      [first]
      [second]
      [first] ..> [second] : depends on

      """

  Scenario: Suppport for legacy docker-compose format
    Given a file named "compose.yml" with:
      """
      first:
        links:
          - second
      second: {}
      """
    When I run `bin/compose_plantuml --link-graph compose.yml`
    Then it should pass with exactly:
      """
      skinparam componentStyle uml2
      [first]
      [second]
      [first] --> [second]

      """

