<script lang="ts">
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { apiFetch } from '#utils/api.js';
	import { Button } from '#lib/components/ui/button';
	import { Card } from '#lib/components/ui/card';
	import { Bookmark, BookmarkCheck, Clock3, Flame, ShoppingCart, Users } from '@lucide/svelte';

	type ShoppingLine = {
		ingredient: string;
		quantity?: string;
		products?: Array<{
			title?: string;
			primary_offer?: { offer_price?: number | string };
			product_page_url?: string;
		}>;
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

	type Meal = {
		name?: string;
		estimated_calories_kcal_per_person?: number;
		ingredients?: string[];
		prep_time?: number;
		Recipe?: string[] | string;
		shopping_list?: ShoppingLine[];
	};

	type MealPlan = {
		id?: string;
		saved_meal_plan?: MealPlan;
		meal_plan?: {
			days?: number;
			people?: number;
			diet?: string;
			daily_meals?: Array<{
				day?: number;
				meals?: Record<string, Meal>;
			}>;
		};
		grocery_list?: Array<{ item: string; quantity: string }>;
	};

	let mealPlan = $state<MealPlan | null>(null);
	let loadError = $state('');
	let savedMealIds = $state<Record<string, string>>({});
	let saveError = $state('');
	let savingMealKey = $state('');
	let cartItems = $state<CartItem[]>([]);
	let cartError = $state('');
	let cartMessage = $state('');
	let isCartReady = $state(false);
	let addingCartMealKey = $state('');
	let isCartUpdating = $state(false);

	onMount(() => {
		void loadMealPlan();
		void loadSavedMeals();
		void loadCart();
	});

	async function loadMealPlan() {
		const id = page.params.slug ?? '';
		const storedData = sessionStorage.getItem(`meal-plan-shopping:${id}`);

		if (storedData) {
			try {
				const parsed = JSON.parse(storedData) as { mealPlan?: MealPlan };
				const savedMealPlan = parsed.mealPlan?.saved_meal_plan ?? parsed.mealPlan;
				if (savedMealPlan?.meal_plan?.daily_meals) {
					mealPlan = savedMealPlan;
					return;
				}
				throw new Error('The generated meal plan did not include any recipes.');
			} catch (error) {
				loadError =
					error instanceof Error
						? error.message
						: 'The generated meal plan could not be read.';
				return;
			}
		}

		try {
			const response = await apiFetch('http://localhost:5001/api/meal-plans');
			const result = await response.json();
			if (!response.ok) {
				throw new Error(result.error ?? 'Could not load the saved meal plan.');
			}

			const savedPlan = result.meal_plans?.find(
				(plan: MealPlan) => plan.id === id
			) as MealPlan | undefined;
			if (!savedPlan?.meal_plan?.daily_meals) {
				throw new Error('This meal plan could not be found.');
			}
			mealPlan = savedPlan;
		} catch (error) {
			loadError =
				error instanceof Error
					? error.message
					: 'Could not load the saved meal plan.';
		}
	}

	function savedMealKey(day: number, mealType: string) {
		return `${page.params.slug}:${day}:${mealType}`;
	}

	async function loadSavedMeals() {
		try {
			const response = await apiFetch('http://localhost:5001/api/saved-meals');
			const result = await response.json();
			if (!response.ok) {
				throw new Error(result.error ?? 'Could not load saved meals.');
			}

			const saved: Record<string, string> = {};
			for (const meal of result.saved_meals ?? []) {
				if (
					meal.id &&
					meal.source_meal_plan_id &&
					meal.day &&
					meal.meal_type
				) {
					saved[`${meal.source_meal_plan_id}:${meal.day}:${meal.meal_type}`] = meal.id;
				}
			}
			savedMealIds = saved;
		} catch (error) {
			saveError = error instanceof Error ? error.message : 'Could not load saved meals.';
		}
	}

	async function toggleSavedMeal(meal: Meal, mealType: string, day: number) {
		const key = savedMealKey(day, mealType);
		const savedId = savedMealIds[key];
		savingMealKey = key;
		saveError = '';
		try {
			const response = await apiFetch(
				savedId
					? `http://localhost:5001/api/saved-meals/${encodeURIComponent(savedId)}`
					: 'http://localhost:5001/api/saved-meals',
				savedId
					? { method: 'DELETE' }
					: {
							method: 'POST',
							headers: { 'Content-Type': 'application/json' },
							body: JSON.stringify({
								meal,
								meal_type: mealType,
								day,
								source_meal_plan_id: page.params.slug
							})
						}
			);
			const result = await response.json();
			if (!response.ok) {
				throw new Error(result.error ?? 'Could not update saved meal.');
			}

			const nextSavedIds = { ...savedMealIds };
			if (savedId) {
				delete nextSavedIds[key];
			} else if (result.saved_meal?.id) {
				nextSavedIds[key] = result.saved_meal.id;
			}
			savedMealIds = nextSavedIds;
		} catch (error) {
			saveError = error instanceof Error ? error.message : 'Could not update saved meal.';
		} finally {
			savingMealKey = '';
		}
	}

	function getPrice(product: NonNullable<ShoppingLine['products']>[number]) {
		const price = Number(product.primary_offer?.offer_price);
		return Number.isFinite(price) ? price : null;
	}

	function getCheapestShoppingItems(meal: Meal, mealType: string, day: number) {
		return (meal.shopping_list ?? []).flatMap((line) => {
			const product = [...(line.products ?? [])]
				.filter((candidate) => getPrice(candidate) !== null)
				.sort((first, second) => (getPrice(first) ?? 0) - (getPrice(second) ?? 0))[0];
			if (!product) return [];
			const productUrl = product.product_page_url;
			return [{
				id: `${page.params.slug}:${day}:${mealType}:${line.ingredient}:${productUrl ?? product.title ?? ''}`,
				title: product.title ?? line.ingredient,
				meal_name: meal.name ?? mealType,
				ingredient: line.ingredient,
				quantity: 1,
				price: getPrice(product),
				product_page_url: productUrl,
				retailer: 'Walmart'
			} satisfies CartItem];
		});
	}

	async function loadCart() {
		try {
			const response = await apiFetch('http://localhost:5001/api/cart');
			const result = await response.json();
			if (!response.ok) {
				throw new Error(result.error ?? 'Could not load your shopping cart.');
			}
			if (!Array.isArray(result.items)) {
				throw new Error('The shopping cart response was invalid.');
			}
			cartItems = result.items;
		} catch (error) {
			cartError = error instanceof Error ? error.message : 'Could not load your shopping cart.';
		} finally {
			isCartReady = true;
		}
	}

	async function addMealItemsToCart(meal: Meal, mealType: string, day: number) {
		const key = savedMealKey(day, mealType);
		addingCartMealKey = key;
		isCartUpdating = true;
		cartError = '';
		cartMessage = '';
		try {
			const itemsToAdd = getCheapestShoppingItems(meal, mealType, day);
			if (itemsToAdd.length === 0) {
				throw new Error('No priced Walmart products were found for this meal.');
			}

			const nextItems = [...cartItems];
			for (const item of itemsToAdd) {
				const existing = nextItems.find((cartItem) => cartItem.id === item.id);
				if (existing) {
					existing.quantity = Math.min(99, existing.quantity + 1);
				} else {
					nextItems.push(item);
				}
			}
			const response = await apiFetch('http://localhost:5001/api/cart', {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ items: nextItems })
			});
			const result = await response.json();
			if (!response.ok) {
				throw new Error(result.error ?? 'Could not add meal ingredients to your cart.');
			}
			cartItems = result.items;
			cartMessage = `Added all ${itemsToAdd.length} available ingredients for ${meal.name ?? mealType}.`;
		} catch (error) {
			cartError = error instanceof Error ? error.message : 'Could not add meal ingredients to your cart.';
		} finally {
			addingCartMealKey = '';
			isCartUpdating = false;
		}
	}

	function getRecipeSteps(recipe: Meal['Recipe']) {
		if (Array.isArray(recipe)) return recipe.filter((step) => step.trim());
		return typeof recipe === 'string'
			? recipe.split(/\r?\n/).map((step) => step.trim()).filter(Boolean)
			: [];
	}
</script>

<svelte:head>
	<title>Meal plan recipes</title>
	<meta name="description" content="Recipes and cooking instructions for your generated meal plan." />
</svelte:head>

<main class="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
	{#if loadError}
		<section class="rounded-xl border p-6" role="alert">
			<h1 class="text-xl font-semibold">Recipes unavailable</h1>
			<p class="mt-2 text-sm text-muted-foreground">{loadError}</p>
			<Button class="mt-4" variant="outline" href="/logged-in-app/meal-plans">
				Back to My Meal Plans
			</Button>
		</section>
	{:else if mealPlan?.meal_plan}
		<header class="mb-8 flex flex-wrap items-start justify-between gap-4">
			<div>
				<p class="text-sm font-semibold uppercase tracking-wide text-primary">Your recipes</p>
				<h1 class="mt-2 text-3xl font-bold tracking-tight">
					{mealPlan.meal_plan.diet || 'Generated meal plan'}
				</h1>
				<div class="mt-3 flex flex-wrap gap-4 text-sm text-muted-foreground">
					{#if mealPlan.meal_plan.days}
						<span>{mealPlan.meal_plan.days} {mealPlan.meal_plan.days === 1 ? 'day' : 'days'}</span>
					{/if}
					{#if mealPlan.meal_plan.people}
						<span class="inline-flex items-center gap-1.5">
							<Users class="size-4" />
							{mealPlan.meal_plan.people}
							{mealPlan.meal_plan.people === 1 ? 'person' : 'people'}
						</span>
					{/if}
				</div>
			</div>
			<Button href={`/logged-in-app/meal-plans-shopping/${page.params.slug}`}>
				<ShoppingCart class="mr-2 size-4" />
				Go to Shopping List
			</Button>
		</header>

		{#if saveError}
			<p class="mb-4 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive" role="alert">
				{saveError}
			</p>
		{/if}
		{#if cartError}
			<p class="mb-4 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive" role="alert">
				{cartError}
			</p>
		{/if}
		{#if cartMessage}
			<p class="mb-4 rounded-md border border-primary/20 bg-primary/5 p-3 text-sm" role="status">
				{cartMessage}
			</p>
		{/if}

		<div class="space-y-6">
			{#each mealPlan.meal_plan.daily_meals ?? [] as day, dayIndex (`${day.day ?? dayIndex}`)}
				<section>
					<h2 class="mb-3 text-xl font-semibold">Day {day.day ?? dayIndex + 1}</h2>
					<div class="space-y-4">
						{#each Object.entries(day.meals ?? {}) as [mealType, meal] (mealType)}
							{@const steps = getRecipeSteps(meal.Recipe)}
							{@const mealDay = day.day ?? dayIndex + 1}
							{@const key = savedMealKey(mealDay, mealType)}
							<Card class="p-5">
								<div class="flex items-start justify-between gap-3">
									<div>
										<p class="text-xs font-semibold uppercase tracking-wide text-primary">{mealType}</p>
										<h3 class="mt-1 text-xl font-semibold">{meal.name ?? 'Meal'}</h3>
									</div>
									<Button
										variant={savedMealIds[key] ? 'secondary' : 'outline'}
										size="sm"
										disabled={savingMealKey === key}
										onclick={() => toggleSavedMeal(meal, mealType, mealDay)}
									>
										{#if savedMealIds[key]}
											<BookmarkCheck class="mr-2 size-4" />
											Saved
										{:else}
											<Bookmark class="mr-2 size-4" />
											Save meal
										{/if}
									</Button>
								</div>
								<div class="mt-3 flex justify-end">
									<Button
										size="sm"
										variant="outline"
										disabled={isCartUpdating || !isCartReady || Boolean(cartError) || !meal.shopping_list?.length}
										onclick={() => addMealItemsToCart(meal, mealType, mealDay)}
									>
										<ShoppingCart class="mr-2 size-4" />
										{addingCartMealKey === key
											? 'Adding all...'
											: 'Add all to cart'}
									</Button>
								</div>
								<div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
									{#if meal.estimated_calories_kcal_per_person}
										<span class="inline-flex items-center gap-1.5">
											<Flame class="size-4" />
											{meal.estimated_calories_kcal_per_person} kcal/person
										</span>
									{/if}
									{#if meal.prep_time}
										<span class="inline-flex items-center gap-1.5">
											<Clock3 class="size-4" />
											{meal.prep_time} min
										</span>
									{/if}
								</div>

								<div class="mt-5 grid gap-5 md:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
									<section>
										<h4 class="font-semibold">Ingredients</h4>
										{#if meal.ingredients?.length}
											<ul class="mt-2 list-inside list-disc space-y-1 text-sm text-muted-foreground">
												{#each meal.ingredients as ingredient, ingredientIndex (`${ingredient}-${ingredientIndex}`)}
													<li>{ingredient}</li>
												{/each}
											</ul>
										{:else}
											<p class="mt-2 text-sm text-muted-foreground">No ingredients listed.</p>
										{/if}
									</section>
									<section>
										<h4 class="font-semibold">Instructions</h4>
										{#if steps.length}
											<ol class="mt-2 list-inside list-decimal space-y-2 text-sm text-muted-foreground">
												{#each steps as step, stepIndex (`${stepIndex}-${step}`)}
													<li>{step}</li>
												{/each}
											</ol>
										{:else}
											<p class="mt-2 text-sm text-muted-foreground">
												Cooking instructions are not available for this recipe.
											</p>
										{/if}
									</section>
								</div>
							</Card>
						{/each}
					</div>
				</section>
			{/each}
		</div>

		<div class="mt-8 flex justify-end">
			<Button href={`/logged-in-app/meal-plans-shopping/${page.params.slug}`}>
				<ShoppingCart class="mr-2 size-4" />
				Go to Shopping List
			</Button>
		</div>
	{:else}
		<p class="py-12 text-center text-sm text-muted-foreground">Loading recipes...</p>
	{/if}
</main>
