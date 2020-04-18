#!jinja|yaml
# -*- coding: utf-8 -*-
# vi: set ft=yaml.jinja :

{% from "lxd/map.jinja" import datamap, sls_block with context %}

include:
  - lxd.python
  - lxd.remotes

{% for remotename, networks in datamap.networks.items() %}
    {%- set remote = datamap.remotes.get(remotename, False) %}

    {%- for name, network in networks.items() %}
lxd_network_{{ remotename }}_{{ name }}:
  lxd_network:
    {%- if 'name' in network %}
    - name: "{{ network['name'] }}"
    {%- else %}
    - name: "{{ name }}"
    {%- endif %}
        {%- if network.get('absent', False) %}
    - absent
        {%- else %}
    - present
        {%- endif %}
        {%- if network.get('description', False) %}
    - description: "{{ network.description }}"
        {%- endif %}
        {%- if network.get('config', False) %}
    - config: {{ network.config | tojson }}
        {%- endif %}
        {%- if remote %}
    - remote_addr: "{{ remote.remote_addr }}"
    - cert: "{{ remote.cert }}"
    - key: "{{ remote.key }}"
    - verify_cert: {{ remote.verify_cert }}
            {%- if remote.get('password', False) %}
    - require:
      - lxd: lxd_remote_{{ remotename }}
            {%- endif %}
        {%- endif %}
        {%- if 'opts' in network %}
    {{ sls_block(network.opts )}}
        {%- endif %}
    {%- endfor %}
{%- endfor %}
