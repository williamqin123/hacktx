
<script lang="ts">
    // @ts-ignore
    import { Button } from "#lib/components/ui/button";
    import {
        Card,
        CardContent,
        CardDescription,
        CardHeader,
        CardTitle
    // @ts-ignore
    } from "#lib/components/ui/card";
    // @ts-ignore
    import { Label } from "#lib/components/ui/label";
    // @ts-ignore
    import { Textarea } from "#lib/components/ui/textarea";
    import { Separator } from "#lib/components/ui/separator";

    import { apiFetch } from "#utils/api.js";
    import { onMount } from "svelte";
    import { LoaderCircle, Sparkles } from "@lucide/svelte";

    // Main request
    let description = $state("");
    let numPeople = $state(1);
    let numDays = $state(1);

    let age = $state<number | undefined>(undefined);
    let sex = $state("");
    let height = $state<number | undefined>(undefined);
    let weight = $state<number | undefined>(undefined);
    let activityLevel = $state("sedentary");
    let dietaryRestrictions = $state<string[]>([]);

    // Saved profile defaults
    let dietGoal = $state("maintain");
    let exclusions = $state("");

    let isLoadingProfile = $state(true);
    let isOnboardingProfilePending = $state(false);
    let isSubmitting = $state(false);
    let errorMessage = $state("");

    async function submit(event: SubmitEvent) {
        event.preventDefault();

        if (!description.trim()) {
            errorMessage = "Please describe the dish or provide ingredients.";
            return;
        }

        if (!Number.isInteger(numPeople) || numPeople < 1 || numPeople > 100) {
            errorMessage = "Please enter a number of people between 1 and 100.";
            return;
        }

        if (!Number.isInteger(numDays) || numDays < 1 || numDays > 30) {
            errorMessage = "Please enter a number of days between 1 and 30.";
            return;
        }

        errorMessage = "";
        isSubmitting = true;

        try {
            const response = await apiFetch(
                "api/meal-plan",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        diet: description.trim(),
                        dietaryRestrictions,
                        goal: dietGoal,
                        age,
                        sex,
                        height,
                        weight,
                        dislikes: exclusions,
                        activityLevel,
                        people: numPeople,
                        days: numDays
                    })
                }
            );

            const responseData = await response.json();
            if (!response.ok) {
                throw new Error(
                    responseData.details ??
                        responseData.error ??
                        "Failed to generate meal plan."
                );
            }

            if (!Array.isArray(responseData.grocery_list)) {
                throw new Error("Meal plan did not include a grocery list.");
            }

            const slug = responseData.saved_meal_plan?.id;
            if (typeof slug !== "string" || !slug) {
                throw new Error("Meal plan was generated but not saved.");
            }

            sessionStorage.setItem(
                `meal-plan-shopping:${slug}`,
                JSON.stringify({
                    mealPlan: responseData,
                    walmartResults: responseData.walmart_results ?? {}
                })
            );
            window.location.assign(
                `/logged-in-app/meal-plan-recipes/${slug}`
            );
        } catch (error) {
            errorMessage =
                error instanceof Error
                    ? error.message
                    : "Something went wrong.";
        } finally {
            isSubmitting = false;
        }
    }

    async function loadProfile() {
        isLoadingProfile = true;
        errorMessage = "";

        try {
            const response = await apiFetch(
                "get-profile-info"
            );

            if (response.status === 404) {
                // No saved profile exists; keep default values.
                return;
            }

            if (!response.ok) {
                throw new Error("Failed to load profile.");
            }

            const profile = await response.json();

            age = profile.age ?? undefined;
            sex = profile.sex ?? "";
            height = profile.height ?? undefined;
            weight = profile.weight ?? undefined;
            dietaryRestrictions = profile.dietaryRestrictions ?? [];
            dietGoal = profile.goal ?? "maintain";
            activityLevel = profile.activityLevel ?? "sedentary";
            exclusions = profile.dislikes ?? "";
        } catch (error) {
            errorMessage =
                error instanceof Error
                    ? error.message
                    : "Failed to load profile.";
        } finally {
            isLoadingProfile = false;
        }
    }

    async function initializeProfile() {
        const pendingProfile = sessionStorage.getItem("pending-onboarding-profile");
        if (!pendingProfile) {
            await loadProfile();
            return;
        }

        isOnboardingProfilePending = true;
        isLoadingProfile = true;
        errorMessage = "";
        try {
            const profile = JSON.parse(pendingProfile);
            const response = await apiFetch(
                "set-profile-info",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: pendingProfile
                }
            );
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error ?? "Failed to save your onboarding profile.");
            }

            age = profile.age ?? undefined;
            sex = profile.sex ?? "";
            height = profile.height ?? undefined;
            weight = profile.weight ?? undefined;
            activityLevel = profile.activityLevel ?? "sedentary";
            dietaryRestrictions = profile.dietaryRestrictions ?? [];
            dietGoal = profile.goal ?? "maintain";
            exclusions = profile.dislikes ?? "";
            sessionStorage.removeItem("pending-onboarding-profile");
            isOnboardingProfilePending = false;
        } catch (error) {
            errorMessage =
                error instanceof Error
                    ? error.message
                    : "Could not save your onboarding profile.";
        } finally {
            isLoadingProfile = false;
        }
    }

    onMount(() => {
        void initializeProfile();
    });
</script>

<svelte:head>
    <title>Prandium AI — Ask the Chef</title>
    <meta
        name="description"
        content="Create a personalized meal plan based on your preferences and serving size."
    />
</svelte:head>

<main class="flex min-h-screen items-center justify-center bg-muted/40 px-4 py-10">
    <Card class="w-full max-w-2xl shadow-lg">
        <CardHeader class="space-y-2 text-center">
            <div class="mb-2 flex items-center justify-center gap-2 text-primary">
                <Sparkles class="size-5" />
                <span class="text-sm font-semibold tracking-wide">Prandium AI</span>
            </div>
            <CardTitle class="text-3xl font-bold">Ask the Chef</CardTitle>
            <CardDescription class="text-sm">
                Tell us what you want to eat, and we'll help you create a meal plan.
            </CardDescription>
        </CardHeader>

        <CardContent>
            <form onsubmit={submit} class="space-y-8" aria-busy={isSubmitting}>
                <section class="space-y-4">
                    <div class="space-y-1">
                        <h2 class="text-lg font-semibold">
                            What kind of food?
                        </h2>
                        <p class="text-sm text-muted-foreground">
                            Describe your dishes, ingredients, or cooking instructions.
                        </p>
                    </div>

                    <div class="space-y-2">
                        <Label for="dish-instructions">
                            Instructions
                        </Label>
                        <Textarea
                            id="dish-instructions"
                            bind:value={description}
                            placeholder="e.g. Suggest quick dinners..."
                            rows={5}
                            required
                        />
                    </div>

                    <!-- Serving size and meal plan duration -->
                    <div class="grid grid-cols-2 gap-4">
                        <div class="space-y-2">
                            <Label for="num-people">
                                Number of People
                            </Label>
                            <input
                                id="num-people"
                                type="number"
                                bind:value={numPeople}
                                min="1"
                                max="100"
                                step="1"
                                required
                                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            />
                            <p class="text-sm text-muted-foreground">
                                People to feed.
                            </p>
                        </div>

                        <div class="space-y-2">
                            <Label for="num-days">
                                Number of Days
                            </Label>
                            <input
                                id="num-days"
                                type="number"
                                bind:value={numDays}
                                min="1"
                                max="30"
                                step="1"
                                required
                                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            />
                            <p class="text-sm text-muted-foreground">
                                Duration of the meal plan.
                            </p>
                        </div>
                    </div>
                </section>

                <Separator />

                {#if errorMessage}
                    <p class="text-sm text-destructive" role="alert">
                        {errorMessage}
                    </p>
                    {#if isOnboardingProfilePending}
                        <Button
                            type="button"
                            variant="outline"
                            onclick={initializeProfile}
                            disabled={isLoadingProfile}
                        >
                            Retry profile save
                        </Button>
                    {/if}
                {/if}

                <Button
                    type="submit"
                    class="w-full"
                    disabled={isSubmitting || isLoadingProfile || isOnboardingProfilePending}
                >
                    {#if isSubmitting}
                        <LoaderCircle class="mr-2 size-4 animate-spin" aria-hidden="true" />
                        Creating your meal plan...
                    {:else}
                        <Sparkles class="mr-2 size-4" aria-hidden="true" />
                        Generate Meal Plan
                    {/if}
                </Button>
                {#if isSubmitting}
                    <section
                        class="generation-status"
                        role="status"
                        aria-live="polite"
                        aria-label="Creating your personalized meal plan"
                    >
                        <div class="generation-status__glow" aria-hidden="true"></div>
                        <div class="generation-status__icon" aria-hidden="true">
                            <LoaderCircle class="size-6 animate-spin" />
                        </div>
                        <div class="min-w-0 flex-1">
                            <p class="font-semibold">Creating your personalized meal plan</p>
                            <p class="mt-1 text-sm text-muted-foreground">
                                Prandium AI is shaping recipes and organizing your shopping list.
                            </p>
                            <div class="generation-status__track mt-4" aria-hidden="true">
                                <span></span>
                            </div>
                        </div>
                    </section>
                {/if}
            </form>
        </CardContent>
    </Card>
</main>

<style>
    .generation-status {
        position: relative;
        display: flex;
        align-items: center;
        gap: 1rem;
        overflow: hidden;
        border: 1px solid color-mix(in oklab, var(--primary) 24%, var(--border));
        border-radius: 1rem;
        padding: 1.1rem;
        background: color-mix(in oklab, var(--primary) 5%, var(--card));
        animation: generation-enter 240ms ease-out both;
    }

    .generation-status__glow {
        position: absolute;
        top: -4rem;
        right: -2rem;
        width: 10rem;
        height: 10rem;
        border-radius: 9999px;
        background: color-mix(in oklab, var(--primary) 12%, transparent);
        filter: blur(32px);
        pointer-events: none;
    }

    .generation-status__icon {
        z-index: 1;
        display: grid;
        width: 2.75rem;
        height: 2.75rem;
        flex: 0 0 auto;
        place-items: center;
        border-radius: 0.85rem;
        background: var(--primary);
        color: var(--primary-foreground);
    }

    .generation-status__track {
        height: 0.25rem;
        overflow: hidden;
        border-radius: 9999px;
        background: color-mix(in oklab, var(--primary) 14%, var(--background));
    }

    .generation-status__track span {
        display: block;
        width: 38%;
        height: 100%;
        border-radius: inherit;
        background: var(--primary);
        animation: generation-progress 1.5s ease-in-out infinite;
    }

    @keyframes generation-enter {
        from {
            opacity: 0;
            transform: translateY(6px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes generation-progress {
        0% {
            transform: translateX(-110%);
        }
        55% {
            transform: translateX(170%);
        }
        100% {
            transform: translateX(300%);
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .generation-status {
            animation: none;
        }

        .generation-status__track span {
            animation: none;
            width: 100%;
        }
    }
</style>
