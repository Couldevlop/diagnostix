{{/*
Expand the name of the chart.
*/}}
{{- define "nexus-diagnostix.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "nexus-diagnostix.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Chart label
*/}}
{{- define "nexus-diagnostix.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "nexus-diagnostix.labels" -}}
helm.sh/chart: {{ include "nexus-diagnostix.chart" . }}
{{ include "nexus-diagnostix.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "nexus-diagnostix.selectorLabels" -}}
app.kubernetes.io/name: {{ include "nexus-diagnostix.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
PostgreSQL hostname (Bitnami subchart, architecture standalone dans notre config)
*/}}
{{- define "nexus-diagnostix.postgresHost" -}}
{{- printf "%s-postgresql" .Release.Name }}
{{- end }}

{{/*
Redis hostname (Bitnami subchart, architecture standalone → service *-redis)
*/}}
{{- define "nexus-diagnostix.redisHost" -}}
{{- printf "%s-redis" .Release.Name }}
{{- end }}

{{/*
Nom du ConfigMap
*/}}
{{- define "nexus-diagnostix.configmapName" -}}
{{- printf "%s-config" (include "nexus-diagnostix.fullname" .) }}
{{- end }}

{{/*
Nom du Secret
*/}}
{{- define "nexus-diagnostix.secretName" -}}
{{- printf "%s-secret" (include "nexus-diagnostix.fullname" .) }}
{{- end }}
