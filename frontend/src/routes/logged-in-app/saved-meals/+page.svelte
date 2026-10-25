<script lang="ts">
	import { onMount } from 'svelte';
	import { apiFetch } from '#utils/api.js';
	import { Button } from '#lib/components/ui/button';
	import { Card } from '#lib/components/ui/card';
	import { Bookmark, ShoppingCart, Trash2 } from '@lucide/svelte';

	type Product = {
		title?: string;
		primary_offer?: { offer_price?: number | string };
		product_page_url?: string;
	};

	type ShoppingLine = {
		ingredient: string;
		quantity?: string;
		products?: Product[];
	};

	type SavedMeal = {
		id: string;
		name: string;
		meal_type: string;
		day: number;
		estimated_calories_kcal_per_person?: number;
		ingredients: string[];
		prep_time?: number;
		Recipe?: string[] | string;
		shopping_list?: ShoppingLine[];
	};

	type CartItem = {
		id: string;
		title: string;
		meal_name: string;
		ingredient: string;
		quantity: number;
		price: number | null;
		product_page_url?: string;
		retailer?: 'Walmart' | 'Kroger';
	};

	let savedMeals = $state<SavedMeal[]>([]);
	let cartItems = $state<CartItem[]>([]);
	let loading = $state(true);
	let loadError = $state('');
	let isCartReady = $state(false);
	let actionError = $state('');
	let busyMealId = $state('');

	onMount(() => {
		void loadSavedMeals();
		void loadCart();
	});

	async function loadSavedMeals() {
		loading = true;
		loadError = '';
		try {
			const response = await apiFetch('api/saved-meals');
			const result = await response.json();
			if (!response.ok) {
				throw new Error(result.error ?? 'Could not load saved meals.');
			}
			if (!Array.isArray(result.saved_meals)) {
				throw new Error('The response did not include saved meals.');
			}
			savedMeals = result.saved_meals;
		} catch (error) {
			loadError = error instanceof Error ? error.message : 'Could not load saved meals.';
		} finally {
			loading = false;
		}
	}

	async function loadCart() {
		try {
			const response = await apiFetch('api/cart');
			const result = await response.json();
			if (!response.ok) {
				throw new Error(result.error ?? 'Could not load your cart.');
			}
			if (!Array.isArray(result.items)) {
				throw new Error('The cart response was invalid.');
			}
			cartItems = result.items;
		} catch (error) {
			actionError = error instanceof Error ? error.message : 'Could not load your cart.';
		} finally {
			isCartReady = true;
		}
	}

	function getRecipeSteps(recipe: SavedMeal['Recipe']) {
		if (Array.isArray(recipe)) return recipe.filter((step) => step.trim());
		return typeof recipe === 'string'
			? recipe.split(/\r?\n/).map((step) => step.trim()).filter(Boolean)
			: [];
	}

	function getPrice(product: Product) {
		const price = Number(product.primary_offer?.offer_price);
		return Number.isFinite(price) ? price : null;
	}

	function cheapestProduct(products: Product[] = []) {
		return [...products].sort((first, second) => {
			const firstPrice = getPrice(first);
			const secondPrice = getPrice(second);
			if (firstPrice === null) return secondPrice === null ? 0 : 1;
			if (secondPrice === null) return -1;
			return firstPrice - secondPrice;
		})[0];
	}

	async function saveCartItems(nextItems: CartItem[]) {
		actionError = '';
		const response = await apiFetch('api/cart', {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ items: nextItems })
		});
		const result = await response.json();
		if (!response.ok) {
			throw new Error(result.error ?? 'Could not update your cart.');
		}
		cartItems = result.items;
	}

	async function addMealToCart(meal: SavedMeal) {
		actionError = '';
		busyMealId = meal.id;
		try {
			const nextItems = [...cartItems];
			for (const line of meal.shopping_list ?? []) {
				const product = cheapestProduct(line.products);
				const productUrl = product?.product_page_url;
				const id = `${meal.id}:${line.ingredient}:${productUrl ?? product?.title ?? ''}`;
				const existing = nextItems.find((item) => item.id === id);
				if (existing) {
					existing.quantity = Math.min(99, existing.quantity + 1);
					continue;
				}
				nextItems.push({
					id,
					title: product?.title ?? line.ingredient,
					meal_name: meal.name,
					ingredient: line.ingredient,
					quantity: 1,
					price: product ? getPrice(product) : null,
					product_page_url: productUrl,
					retailer: 'Walmart'
				});
			}
			await saveCartItems(nextItems);
		} catch (error) {
			actionError = error instanceof Error ? error.message : 'Could not add this meal to your cart.';
		} finally {
			busyMealId = '';
		}
	}

	async function deleteSavedMeal(id: string) {
		actionError = '';
		busyMealId = id;
		try {
			const response = await apiFetch(
				`http://localhost:5001/api/saved-meals/${encodeURIComponent(id)}`,
				{ method: 'DELETE' }
			);
			const result = await response.json();
			if (!response.ok) {
				throw new Error(result.error ?? 'Could not remove this saved meal.');
			}
			savedMeals = savedMeals.filter((meal) => meal.id !== id);
		} catch (error) {
			actionError = error instanceof Error ? error.message : 'Could not remove this saved meal.';
		} finally {
			busyMealId = '';
		}
	}

</script>

<svelte:head>
	<title>Saved Meals</title>
	<meta name="description" content="Your saved recipes and meal ingredients." />
</svelte:head>

<main class="mx-auto w-full max-w-6xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
	<header>
		<h1 class="text-3xl font-bold tracking-tight">Saved Meals</h1>
		<p class="mt-2 text-muted-foreground">
			Keep recipes you love and add their ingredients to your shopping cart.
		</p>
		<Button class="mt-4" variant="outline" href="/logged-in-app/shopping-cart">
			<ShoppingCart class="mr-2 size-4" />
			View shopping cart
		</Button>
	</header>

	{#if actionError}
		<p class="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive" role="alert">
			{actionError}
		</p>
	{/if}

	<section aria-labelledby="saved-meals-heading">
		<div class="mb-4 flex items-center gap-2">
			<Bookmark class="size-5 text-primary" />
			<h2 id="saved-meals-heading" class="text-xl font-semibold">Your meals</h2>
		</div>
		{#if loading}
			<p class="py-8 text-center text-sm text-muted-foreground">Loading saved meals...</p>
		{:else if loadError}
			<p class="rounded-xl border p-5 text-sm text-destructive" role="alert">{loadError}</p>
		{:else if savedMeals.length === 0}
			<div class="rounded-xl border border-dashed p-8 text-center">
				<p class="font-medium">No saved meals yet</p>
				<p class="mt-2 text-sm text-muted-foreground">
					Save a recipe from a generated meal plan and it will show up here.
				</p>
				<Button class="mt-4" variant="outline" href="/logged-in-app/meal-plans">
					View meal plans
				</Button>
			</div>
		{:else}
			<div class="grid gap-5 lg:grid-cols-2">
				{#each savedMeals as meal (meal.id)}
					<Card class="space-y-5 p-5">
						<header class="flex flex-wrap items-start justify-between gap-3">
							<div>
								<p class="text-xs font-semibold uppercase tracking-wide text-primary">
									Day {meal.day} · {meal.meal_type}
								</p>
								<h3 class="mt-1 text-xl font-semibold">{meal.name}</h3>
								<p class="mt-1 text-sm text-muted-foreground">
									{meal.prep_time ?? '—'} min
									{#if meal.estimated_calories_kcal_per_person}
										· {meal.estimated_calories_kcal_per_person} kcal/person
									{/if}
								</p>
							</div>
							<Button
								variant="ghost"
								size="icon"
								aria-label={`Remove ${meal.name} from saved meals`}
								title="Remove saved meal"
								disabled={busyMealId === meal.id}
								onclick={() => deleteSavedMeal(meal.id)}
							>
								<Trash2 class="size-4 text-destructive" />
							</Button>
						</header>

						<div class="grid gap-5 sm:grid-cols-2">
							<section>
								<h4 class="font-semibold">Ingredients</h4>
								<ul class="mt-2 list-inside list-disc space-y-1 text-sm text-muted-foreground">
									{#each meal.ingredients ?? [] as ingredient, ingredientIndex (`${ingredient}-${ingredientIndex}`)}
										<li>{ingredient}</li>
									{/each}
								</ul>
							</section>
							<section>
								<h4 class="font-semibold">Instructions</h4>
								<ol class="mt-2 list-inside list-decimal space-y-1 text-sm text-muted-foreground">
									{#each getRecipeSteps(meal.Recipe) as step, index (`${index}-${step}`)}
										<li>{step}</li>
									{:else}
										<li class="list-none">No instructions are available.</li>
									{/each}
								</ol>
							</section>
						</div>

						<div class="flex items-center justify-between gap-3 border-t pt-4">
							<p class="text-sm text-muted-foreground">
								{meal.shopping_list?.length ?? 0} shopping ingredients
							</p>
							<Button
								size="sm"
								disabled={busyMealId === meal.id || !isCartReady || !meal.shopping_list?.length}
								onclick={() => addMealToCart(meal)}
							>
								<ShoppingCart class="mr-2 size-4" />
								{busyMealId === meal.id ? 'Adding...' : 'Add meal to cart'}
							</Button>
						</div>
					</Card>
				{/each}
			</div>
		{/if}
	</section>

</main>
