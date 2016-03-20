[![Build Status](https://travis-ci.org/funkwerk/compose_plantuml.svg)](https://travis-ci.org/funkwerk/compose_plantuml)
[![](https://badge.imagelayers.io/funkwerk/compose_plantuml.svg)](https://imagelayers.io/?images=funkwerk/compose_plantuml:latest 'funkwerk/compose_plantuml')
[![PyPi downloads](https://img.shields.io/pypi/dm/compose_plantuml.svg)](https://pypi.python.org/pypi/compose_plantuml/)
[![PyPi version](https://img.shields.io/pypi/v/compose_plantuml.svg)](https://pypi.python.org/pypi/compose_plantuml/)
[![Docker pulls](https://img.shields.io/docker/pulls/funkwerk/compose_plantuml.svg)](https://hub.docker.com/r/funkwerk/compose_plantuml/)

# compose_plantuml

Generate Plantuml graphs from docker-compose files

Currently just docker-compose version 2 is supported.

## Usage

### Via Python

Install it via:
`pip3 install compose_plantuml`

After that use it like:
`compose_plantuml docker-compose.yml`

### Via Docker

Use it like:
`cat docker-compose.yml | docker run -i funkwerk/compose_plantuml`

## Link Graph

Link Graphs provide an overview over docker-compose services.

Consider the following docker-compose.yml

```
version: '2'
services:
  first:
    links:
      - second
  second: {}
```

When calling 'compose_plantuml docker-compose.yml' it will generate the following link graph:

```
[first]
[second]
[first] --> [second]
```

Rendered it looks like:

<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" height="149px" style="width:87px;height:149px;" version="1.1" viewBox="0 0 87 149" width="87px"><defs><filter height="300%" id="f1" width="300%" x="-1" y="-1"><feGaussianBlur result="blurOut" stdDeviation="2.0"/><feColorMatrix in="blurOut" result="blurOut2" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 .4 0"/><feOffset dx="4.0" dy="4.0" in="blurOut2" result="blurOut3"/><feBlend in="SourceGraphic" in2="blurOut3" mode="normal"/></filter></defs><g><rect fill="#FEFECE" filter="url(#f1)" height="36.2969" style="stroke: #A80036; stroke-width: 1.5;" width="45" x="19.5" y="8"/><rect fill="#FEFECE" height="5" style="stroke: #A80036; stroke-width: 1.5;" width="10" x="14.5" y="13"/><rect fill="#FEFECE" height="5" style="stroke: #A80036; stroke-width: 1.5;" width="10" x="14.5" y="34.2969"/><text fill="#000000" font-family="sans-serif" font-size="14" lengthAdjust="spacingAndGlyphs" textLength="25" x="29.5" y="30.9951">first</text><rect fill="#FEFECE" filter="url(#f1)" height="36.2969" style="stroke: #A80036; stroke-width: 1.5;" width="72" x="6" y="104"/><rect fill="#FEFECE" height="5" style="stroke: #A80036; stroke-width: 1.5;" width="10" x="1" y="109"/><rect fill="#FEFECE" height="5" style="stroke: #A80036; stroke-width: 1.5;" width="10" x="1" y="130.2969"/><text fill="#000000" font-family="sans-serif" font-size="14" lengthAdjust="spacingAndGlyphs" textLength="52" x="16" y="126.9951">second</text><path d="M42,44.241 C42,59.4791 42,81.8069 42,98.4576 " fill="none" style="stroke: #A80036; stroke-width: 1.0;"/><polygon fill="#A80036" points="42,103.8683,46,94.8683,42,98.8683,38,94.8683,42,103.8683" style="stroke: #A80036; stroke-width: 1.0;"/></g></svg>

## Related Links

 - draw compose
   - https://github.com/Alexis-benoist/draw-compose
   - generates dot graphs from docker-compose files
   - currently just supports docker-compose version 1
   - does not read from stdin, so is not easy useable as docker container
