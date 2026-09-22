{% for role in experience %}

# {{ role.display_title }}

{{ role.employer }}

{% if role.client %}
Client: {{ role.client }}
{% endif %}

{% if role.project %}
Project: {{ role.project }}
{% endif %}

Period: {{ role.start_date }} – {{ role.end_date if role.end_date else "Present" }}

{{ role.summary }}

Key Responsibilities:

{% for responsibility in role.responsibilities[:6] %}
• {{ responsibility }}
{% endfor %}

{% endfor %}