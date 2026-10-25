
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

    let dishInstructions = $state("");
    let isSubmitting = $state(false);
    let errorMessage = $state("");

    import DietaryRestrictionsPicker from '#components/DietaryRestrictionsPicker.svelte';

	let restrictions = $state<string[]>([]);

    async function submit(event: SubmitEvent) {
        event.preventDefault();

        if (!dishInstructions.trim()) {
            errorMessage = "Please describe the dish or provide ingredients.";
            return;
        }

        errorMessage = "";
        isSubmitting = true;

        try {
            const response = await fetch("/api/recipes", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    instructions: dishInstructions.trim(),
                    dietaryRestrictions: dietaryRestrictions.trim()
                })
            });

            if (!response.ok) {
                throw new Error("Failed to generate recipe.");
            }

            const recipe = await response.json();

            // TODO: Store or display the generated recipe.
            console.log("Generated recipe:", recipe);
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

<svelte:head>
    <title>Ask the Chef</title>
    <meta
        name="description"
        content="Generate a recipe based on your ingredients and dietary preferences."
    />
</svelte:head>

<main class="flex min-h-screen items-center justify-center bg-muted/40 px-4 py-10">
    <Card class="w-full max-w-2xl shadow-lg">
        <CardHeader class="space-y-2 text-center">
            <CardTitle class="text-3xl font-bold">
                Ask the Chef
            </CardTitle>
            <CardDescription class="text-sm">
                Tell us what you want to cook, and we'll help you create a recipe.
            </CardDescription>
        </CardHeader>

        <CardContent>
            <form onsubmit={submit} class="space-y-8">
                <section class="space-y-4">
                    <div class="space-y-1">
                        <h2 class="text-lg font-semibold">
                            What Kind of Dish?
                        </h2>
                        <p class="text-sm text-muted-foreground">
                            Describe your dish, ingredients, or cooking instructions.
                        </p>
                    </div>

                    <div class="space-y-2">
                        <Label for="dish-instructions">
                            Dish and Ingredients
                        </Label>
                        <Textarea
                            id="dish-instructions"
                            bind:value={dishInstructions}
                            placeholder="e.g. I have chicken, rice, garlic, and tomatoes. Suggest a quick dinner..."
                            rows={5}
                            required
                        />
                    </div>
                </section>

                <div class="border-t"></div>

                <section class="space-y-4">
                    <DietaryRestrictionsPicker bind:value={restrictions} />
                </section>

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
                    {isSubmitting ? "Generating Recipe..." : "Generate Recipe"}
                </Button>
            </form>
        </CardContent>
    </Card>
</main>
