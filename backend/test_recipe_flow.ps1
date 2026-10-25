param(
    [string]$BaseUrl = "http://127.0.0.1:5000"
)

$ErrorActionPreference = "Stop"
$BaseUrl = $BaseUrl.TrimEnd("/")

$mealPlanRequest = @{
    people = 1
    diet = "balanced"
    days = 1
    dislikes = ""
    age = 30
    sex = "prefer_not_to_say"
    height = 170
    weight = 70
    goal = "maintain"
    activityLevel = "moderately_active"
    dietaryRestrictions = @()
}

try {
    Write-Host "Requesting a meal plan (this may take a minute)..."
    $mealPlan = Invoke-RestMethod `
        -Method Post `
        -Uri "$BaseUrl/api/meal-plan" `
        -ContentType "application/json" `
        -Body ($mealPlanRequest | ConvertTo-Json -Depth 10) `
        -TimeoutSec 180

    $savedRecipes = @($mealPlan.recipes)
    if ($savedRecipes.Count -eq 0) {
        throw "POST /api/meal-plan returned no saved recipes."
    }

    Write-Host "Meal plan returned $($savedRecipes.Count) saved recipe(s). Checking GET..."
    $recipeResult = Invoke-RestMethod `
        -Method Get `
        -Uri "$BaseUrl/api/recipes" `
        -TimeoutSec 30

    $allRecipes = @($recipeResult.recipes)
    $recipeIds = @(
        $allRecipes |
            ForEach-Object { $_.id } |
            Where-Object { $_ }
    )
    $missing = @(
        $savedRecipes |
            Where-Object { $_.id -notin $recipeIds }
    )

    if ($missing.Count -gt 0) {
        throw "GET /api/recipes did not return $($missing.Count) recipe(s) saved by POST."
    }

    Write-Host "PASS: GET /api/recipes returned all $($savedRecipes.Count) recipes saved by POST."
    $savedRecipes |
        Select-Object id, meal_type, name |
        Format-Table -AutoSize
}
catch {
    Write-Error $_
    exit 1
}
