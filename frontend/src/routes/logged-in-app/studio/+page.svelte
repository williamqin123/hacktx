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

    let description = $state("");

	let dietaryRestrictions = $state<string[]>([]);
	let dietGoal = $state('maintain');
	import DietaryRestrictionsPicker from '#components/DietaryRestrictionsPicker.svelte';
	import DietaryGoalPicker from '#components/DietaryGoalPicker.svelte';

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
            const response = await fetch("http://localhost:5001/api/meal-plan", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    description: description.trim(),
                    dietaryRestrictions: dietaryRestrictions,
                    dietGoal: dietGoal
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
                        Override Your Default Dietary Preferences
                        <ChevronDown class="h-4 w-4 transition-transform duration-200 data-[state=open]:rotate-180" />
                    </Collapsible.Trigger>

                    <Collapsible.Content class="space-y-4">
                        <section class="space-y-4">
                            <DietaryRestrictionsPicker bind:value={dietaryRestrictions} />
                            <Separator />
                            <DietaryGoalPicker bind:dietGoal={dietGoal} />
                        </section>
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
