{{- define "challenge.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "challenge.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "challenge.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "challenge.labels" -}}
app.kubernetes.io/name: {{ include "challenge.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end }}

{{- define "challenge.backendName" -}}
{{- printf "%s-backend" (include "challenge.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "challenge.frontendName" -}}
{{- printf "%s-frontend" (include "challenge.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
