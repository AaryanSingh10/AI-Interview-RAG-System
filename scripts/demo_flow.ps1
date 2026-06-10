# Quick smoke test for demo video preparation
$ErrorActionPreference = "Stop"
$base = "http://localhost:8000/api"
$resume = Join-Path $PSScriptRoot "..\knowledge_base\sample_resumes\ml_engineer_resume.txt"

Write-Host "1. Health check"
Invoke-RestMethod "$base/health" | ConvertTo-Json

Write-Host "2. Create session"
$boundary = [System.Guid]::NewGuid().ToString()
$fileBytes = [System.IO.File]::ReadAllBytes($resume)
$bodyLines = @(
    "--$boundary",
    'Content-Disposition: form-data; name="role_id"',
    "",
    "ml_engineer",
    "--$boundary",
    'Content-Disposition: form-data; name="resume"; filename="resume.txt"',
    "Content-Type: text/plain",
    "",
    [System.Text.Encoding]::UTF8.GetString($fileBytes),
    "--$boundary--"
) -join "`r`n"

$session = Invoke-RestMethod -Uri "$base/sessions" -Method Post -ContentType "multipart/form-data; boundary=$boundary" -Body $bodyLines
Write-Host "Session ID: $($session.session_id)"

Write-Host "3. Generate questions"
$questions = Invoke-RestMethod -Uri "$base/sessions/$($session.session_id)/questions" -Method Post
Write-Host "Questions generated: $($questions.questions.Count)"

Write-Host "4. Submit answers"
foreach ($q in $questions.questions) {
    $payload = @{ question_id = $q.id; answer = "Demonstration answer for $($q.topic)" } | ConvertTo-Json
    Invoke-RestMethod -Uri "$base/sessions/$($session.session_id)/answers" -Method Post -Body $payload -ContentType "application/json" | Out-Null
}

Write-Host "5. Complete interview"
$summary = Invoke-RestMethod -Uri "$base/sessions/$($session.session_id)/complete" -Method Post
Write-Host "Overall score: $($summary.overall_score)"
Write-Host "Recommendation: $($summary.recommendation)"
