
<script lang="ts">
	import { onMount } from 'svelte';
	import { Button } from '#lib/components/ui/button';
	import { Card } from '#lib/components/ui/card';
	import { Trash2 } from '@lucide/svelte';

	type Recipe = {
		id: string;
		name: string;
		slug: string;
		image: string;
	};

	let recipes: Recipe[] = $state([]);
	let loading = $state(true);
	let error = $state('');

	onMount(() => {
		loadRecipes();
	});

	async function loadRecipes() {
		loading = true;
		error = '';

		try {
			const response = await fetch('/api/saved-recipes');

			if (!response.ok) {
				throw new Error('Failed to load recipes');
			}

			recipes = await response.json();
		} catch {
			error = 'Could not load your saved recipes.';
		} finally {
			loading = false;
		}
	}

	async function deleteRecipe(id: string) {
		error = '';

		try {
			const response = await fetch(`/api/saved-recipes/${id}`, {
				method: 'DELETE'
			});

			if (!response.ok) {
				throw new Error('Failed to delete recipe');
			}

			recipes = recipes.filter((recipe) => recipe.id !== id);
		} catch {
			error = 'Could not delete the recipe. Please try again.';
		}
	}
</script>

<svelte:head>
	<title>Saved Recipes</title>
</svelte:head>

<div class="mx-auto w-full max-w-7xl p-4 sm:p-6 lg:p-8">
	<header class="mb-6">
		<h1 class="text-2xl font-bold tracking-tight sm:text-3xl">
			Saved Recipes
		</h1>
		<p class="mt-2 text-sm text-muted-foreground">
			Your favorite recipes, all in one place.
		</p>
	</header>

	{#if error}
		<div class="mb-4 flex flex-wrap items-center gap-3">
			<p class="text-sm text-destructive" role="alert">{error}</p>
			{#if !loading && recipes.length === 0}
				<Button variant="outline" size="sm" onclick={loadRecipes}>
					Try again
				</Button>
			{/if}
		</div>
	{/if}

	{#if loading}
		<p class="py-12 text-center text-sm text-muted-foreground">
			Loading saved recipes...
		</p>
	{:else if recipes.length > 0}
		<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-5 lg:grid-cols-4 xl:grid-cols-5">
			{#each recipes as recipe (recipe.id)}
				<Card class="group relative min-w-0 overflow-hidden rounded-xl py-0">
					<a
						href={`/recipes/${recipe.slug}`}
						class="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
						aria-label={`View ${recipe.name}`}
					>
						<img
							src={recipe.image}
							alt={recipe.name}
							loading="lazy"
							class="aspect-square w-full object-cover transition-transform duration-200 group-hover:scale-[1.02]"
						/>
						<h2 class="px-3 py-3 pr-11 text-sm font-semibold leading-snug sm:text-base">
							{recipe.name}
						</h2>
					</a>

					<Button
						variant="ghost"
						size="icon"
						class="absolute bottom-2 right-2 size-8 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
						aria-label={`Delete ${recipe.name}`}
						title="Delete recipe"
						onclick={() => deleteRecipe(recipe.id)}
					>
						<Trash2 class="size-4" />
					</Button>
				</Card>
			{/each}
		</div>
	{:else}
		<div class="flex flex-col items-center justify-center gap-3 py-16 text-center">
			<h2 class="text-lg font-semibold">No saved recipes</h2>
			<p class="text-sm text-muted-foreground">
				Recipes you save will appear here.
			</p>
			<Button variant="outline" href="/recipes">
				Explore recipes
			</Button>
		</div>
	{/if}
</div>
