# Markdown Card

```md
{% set lists = state_attr("sensor.xxx_watch_message_01102xxxxxxxxxxxxxxxxxxxxxxxxxxx", "list") %}
{% for item in lists %}
  {% set data = item.data %}
  {% set sender = item.sender %}
  {% set receiver = item.receiver %}
  {% set type = item.type %}
  {% if type == "SOS" -%}
    <ha-alert title="Type: {{ type }}" alert-type="error">***{{ (data.tm / 1000) | timestamp_custom('%Y-%m-%d %H:%M:%S') }}***</ha-alert>
    Sender: {{ sender.name }}
    Empfänger: {{ receiver.name }}
    <details>
    <summary>{{ type }}</summary>
    {{ data.poi }}
    {{ data.city }}
    {{ data.province }}
    {{ data.country_name }}
    Genauigkeit: {{ data.radius }}m
    {{ data.lat }}
    {{ data.lng }}
    https://www.openstreetmap.org/#map=19/{{ data.lat }}/{{ data.lng }}
    {{ data.locate_type }}
    </details>
  {%- elif type == "TEXT" -%}
    <ha-alert title="Type: {{ type }}" alert-type="info">***{{ (data.tm / 1000) | timestamp_custom('%Y-%m-%d %H:%M:%S') }}***</ha-alert>
    Sender: {{ sender.name }}
    Empfänger: {{ receiver.name }}
    Nachricht: ***{{ data.text }}***
  {%- elif type == "LOW_POWER" -%}
    <ha-alert title="Type: {{ type }}" alert-type="info">***{{ (data.tm / 1000) | timestamp_custom('%Y-%m-%d %H:%M:%S') }}***</ha-alert>
    Sender: {{ sender.name }}
    Empfänger: {{ receiver.name }}
    Nachricht: ***Battery = {{ data.battery }}%***
  {%- elif type == "ARRIVE_SAFE_ZONE" -%}
    <ha-alert title="Type: {{ type }}" alert-type="success">***{{ (data.tm / 1000) | timestamp_custom('%Y-%m-%d %H:%M:%S') }}***</ha-alert>
    Sender: {{ sender.name }}
    Empfänger: {{ receiver.name }}
    <details>
    <summary>{{ type }}</summary>
    {{ data.poi }}
    {{ data.city }}
    {{ data.province }}
    {{ data.country_name }}
    Genauigkeit: {{ data.radius }}m
    {{ data.lat }}
    {{ data.lng }}
    https://www.openstreetmap.org/#map=19/{{ data.lat }}/{{ data.lng }}
    {{ data.locate_type }}
    </details>
  {%- elif type == "LEAVE_SAFE_ZONE" -%}
    <ha-alert title="Type: {{ type }}" alert-type="warning">***{{ (data.tm / 1000) | timestamp_custom('%Y-%m-%d %H:%M:%S') }}***</ha-alert>
    Sender: {{ sender.name }}
    Empfänger: {{ receiver.name }}
    <details>
    <summary>{{ type }}</summary>
    {{ data.poi }}
    {{ data.city }}
    {{ data.province }}
    {{ data.country_name }}
    Genauigkeit: {{ data.radius }}m
    {{ data.lat }}
    {{ data.lng }}
    https://www.openstreetmap.org/#map=19/{{ data.lat }}/{{ data.lng }}
    {{ data.locate_type }}
    </details>
  {%- elif type == "CALL_LOG" -%}
    <ha-alert title="Type: {{ type }}" alert-type="warning">***{{ (data.tm / 1000) | timestamp_custom('%Y-%m-%d %H:%M:%S') }}***</ha-alert>
    Sender: {{ sender.name }}
    Empfänger: {{ receiver.name }}
    Angerufen wurde: {{ data.call_name }}
    Angerufen am/um: {{ data.call_time | timestamp_custom('%Y-%m-%d %H:%M:%S') }}
  {%- else -%}
    <ha-alert title="Type: {{ type }}">***{{ (data.tm / 1000) | timestamp_custom('%Y-%m-%d %H:%M:%S') }}***</ha-alert>
    Sender: {{ sender.name }}
    Empfänger: {{ receiver.name }}
  {%- endif %}  
{% endfor %}
```
