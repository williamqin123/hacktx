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
    import * as Collapsible from "#lib/components/ui/collapsible";
    import { Separator } from "#lib/components/ui/separator";
    import { ChevronDown } from "@lucide/svelte";

    import { apiFetch } from "#utils/api.js";

    let description = $state("");

	let age = $state<number | undefined>(undefined);
	let sex = $state('');
	let height = $state<number | undefined>(undefined);
	let weight = $state<number | undefined>(undefined);
	let activityLevel = $state('sedentary');
	let dietaryRestrictions = $state<string[]>([]);

	let dietGoal = $state('maintain');
    let exclusions = $state<string>('');
	import DietaryGoalPicker from '#components/DietaryGoalPicker.svelte';

    let numPeople = $state(1);

    let isLoadingUserSavedDietaryPreferences = $state(true);
    let isSubmitting = $state(false);
    let errorMessage = $state("");

    async function submit(event: SubmitEvent) {
        event.preventDefault();

        if (!description.trim()) {
            errorMessage = "Please describe the dish or provide ingredients.";
            return;
        }

        errorMessage = "";
        isSubmitting = true;

        try {
            const response = await apiFetch("http://localhost:5001/api/meal-plan", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    diet: description.trim(),
                    dietaryRestrictions: dietaryRestrictions,
                    goal: dietGoal,
                    age,
                    sex,
                    height,
                    weight,
                    dislikes: exclusions,
                    activityLevel,
                    people: numPeople
                })
            });

            if (!response.ok) {
                throw new Error("Failed to generate recipe.");
            }

            const mealPlanUrl = await response.text();
            window.location.assign(mealPlanUrl);

        } catch (error) {
            errorMessage =
                error instanceof Error
                    ? error.message
                    : "Something went wrong.";
        } finally {
            isSubmitting = false;
        }
    }

    import { onMount } from 'svelte';

	async function loadProfile() {
		isLoadingUserSavedDietaryPreferences = true;
		errorMessage = '';

		try {
			const response = await apiFetch(
				'http://localhost:5001/get-profile-info'
			);

			if (response.status === 404) {
				// No profile exists yet; keep the default field values.
				return;
			}

			if (!response.ok) {
				throw new Error('Failed to load profile.');
			}

			const profile = await response.json();

            age = profile.age ?? undefined;
			sex = profile.sex ?? '';
			height = profile.height ?? undefined;
			weight = profile.weight ?? undefined;
			dietaryRestrictions = profile.dietaryRestrictions ?? [];
			dietGoal = profile.goal ?? 'maintain';
            activityLevel = profile.activityLevel ?? 'sedentary';
		} catch (error) {
			errorMessage =
				error instanceof Error
					? error.message
					: 'Failed to load profile.';
		} finally {
			isLoadingUserSavedDietaryPreferences = false;
		}
	}

	onMount(() => {
		loadProfile();
	});
</script>

<main class="flex min-h-screen items-center justify-center bg-muted/40 px-4 py-10">
    <Card class="w-full max-w-2xl shadow-lg">
        <CardHeader class="space-y-2 text-center">
            <CardTitle class="text-3xl font-bold">
                Ask the Chef
            </CardTitle>
            <CardDescription class="text-sm">
                Tell us what you want to eat, and we'll help you create a meal plan.
            </CardDescription>
        </CardHeader>

        <CardContent>
            <form onsubmit={submit} class="space-y-8">
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
                </section>

                <div class="border-t"></div>

                <Collapsible.Root class="space-y-4">
                    <Collapsible.Trigger
                        class="flex w-full items-center justify-between rounded-md py-2 text-sm font-medium hover:underline"
                    >
                        Override Your Saved Dietary Preferences
                        <ChevronDown class="h-4 w-4 transition-transform duration-200 data-[state=open]:rotate-180" />
                    </Collapsible.Trigger>

                    <Collapsible.Content class="space-y-4">
                        {#if isLoadingUserSavedDietaryPreferences}
                        <p class="text-sm text-muted-foreground">
                            Loading your saved dietary preferences...
                        </p>
                        {:else}
                        <section class="space-y-4">
                            <h2 class="text-lg font-semibold">
                                Dislikes / Exclusions
                            </h2>
                            <div class="space-y-2">
                                <Label for="dish-instructions">
                                    Dislikes / Exclusions
                                </Label>
                                <Textarea
                                    id="exclude"
                                    bind:value={exclusions}
                                    placeholder="e.g. No ranch sauce"
                                    rows={3}
                                />
                            </div>
                            <Separator />
                            <DietaryGoalPicker bind:dietGoal={dietGoal} />
                        </section>
                        {/if}
                    </Collapsible.Content>
                </Collapsible.Root>

                {#if errorMessage}
                    <p class="text-sm text-destructive" role="alert">
                        {errorMessage}
                    </p>
                {/if}

                <Button
                    type="submit"
                    class="w-full"
                    disabled={isSubmitting}
                >
                    {isSubmitting ? "Generating..." : "Generate Meal Plan"}
                </Button>
            </form>
        </CardContent>
    </Card>
</main>
