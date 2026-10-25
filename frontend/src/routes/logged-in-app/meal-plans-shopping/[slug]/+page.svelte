<script lang="ts">
	import { page } from '$app/state';
	import { onMount } from 'svelte';

	type GroceryItem = {
		item: string;
		quantity: string;
	};

	type WalmartProduct = {
		title?: string;
		primary_offer?: {
			offer_price?: number | string;
		};
		product_page_url?: string;
	};

	type ProductSearch = {
		organic_results?: WalmartProduct[];
		status?: string;
	};

	type MealPlan = {
		meal_plan?: {
			days?: number;
			people?: number;
			daily_meals?: Array<{
				day?: number;
				meals?: Record<string, { name?: string }>;
			}>;
		};
		grocery_list?: GroceryItem[];
	};

	type ShoppingData = {
		mealPlan: MealPlan;
		walmartResults: Record<string, ProductSearch>;
	};

	let shoppingData = $state<ShoppingData | null>(null);
	let loadError = $state('');

	onMount(() => {
		const slug = page.params.slug;
		const storedData = sessionStorage.getItem(`meal-plan-shopping:${slug}`);
		if (!storedData) {
			loadError = 'This shopping list is no longer available. Generate a new meal plan to create one.';
			return;
		}

		try {
			shoppingData = JSON.parse(storedData) as ShoppingData;
		} catch {
			loadError = 'The saved shopping list could not be read. Generate a new meal plan to try again.';
		}
	});

	function resultKey(groceryItem: GroceryItem) {
		const itemName = groceryItem.item.trim();
		const quantity = groceryItem.quantity.trim();
		return quantity && !itemName.toLocaleLowerCase().includes(quantity.toLocaleLowerCase())
			? `${quantity} ${itemName}`
			: quantity || itemName;
	}

	function getProducts(groceryItem: GroceryItem) {
		return shoppingData?.walmartResults[resultKey(groceryItem)]?.organic_results ?? [];
	}

	function getPrice(product: WalmartProduct) {
		const price = Number(product.primary_offer?.offer_price);
		return Number.isFinite(price) ? price : null;
	}

	const estimatedTotal = $derived(
		(shoppingData?.mealPlan.grocery_list ?? []).reduce((total, item) => {
			const firstProduct = getProducts(item)[0];
			return total + (firstProduct ? (getPrice(firstProduct) ?? 0) : 0);
		}, 0)
	);

	const mealNames = $derived(
		(shoppingData?.mealPlan.meal_plan?.daily_meals ?? []).flatMap((day) =>
			Object.values(day.meals ?? {})
				.map((meal) => meal.name)
				.filter((name): name is string => Boolean(name))
		)
	);
</script>

<svelte:head>
	<title>Meal plan shopping list</title>
	<meta
		name="description"
		content="Walmart product links and estimated prices for your meal plan ingredients."
	/>
</svelte:head>

<main class="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
	<header class="mb-8">
		<p class="text-sm font-semibold uppercase tracking-wide text-primary">Meal plan</p>
		<h1 class="mt-2 text-3xl font-bold tracking-tight">Shopping list</h1>
		<p class="mt-2 text-muted-foreground">
			Ingredient quantities and Walmart product links for your full meal plan.
		</p>
	</header>

	{#if loadError}
		<section class="rounded-xl border p-6" role="alert">
			<h2 class="font-semibold">Shopping list unavailable</h2>
			<p class="mt-2 text-sm text-muted-foreground">{loadError}</p>
			<a
				href="/logged-in-app/studio"
				class="mt-4 inline-flex rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
			>
				Create a meal plan
			</a>
		</section>
	{:else if shoppingData}
		{#if mealNames.length > 0}
			<section class="mb-6 rounded-xl border bg-card p-5">
				<h2 class="font-semibold">Meals in this plan</h2>
				<ul class="mt-3 grid gap-2 text-sm sm:grid-cols-2">
					{#each mealNames as mealName}
						<li>{mealName}</li>
					{/each}
				</ul>
			</section>
		{/if}

		<section class="mb-5 flex flex-wrap items-end justify-between gap-3 rounded-xl border bg-card p-5">
			<div>
				<h2 class="font-semibold">Estimated grocery total</h2>
				<p class="mt-1 text-sm text-muted-foreground">
					Based on the first Walmart result for each ingredient. Prices and availability may change.
				</p>
			</div>
			<p class="text-2xl font-bold">${estimatedTotal.toFixed(2)}</p>
		</section>

		{#if shoppingData.mealPlan.grocery_list?.length}
			<div class="space-y-4">
				{#each shoppingData.mealPlan.grocery_list as groceryItem, index (`${groceryItem.item}-${index}`)}
					{@const products = getProducts(groceryItem)}
					<section class="rounded-xl border bg-card p-5">
						<div class="flex flex-wrap items-baseline justify-between gap-2">
							<h2 class="text-lg font-semibold">{groceryItem.item}</h2>
							<p class="text-sm text-muted-foreground">
								Quantity for the full meal plan: {groceryItem.quantity || 'Not specified'}
							</p>
						</div>

						{#if products.length > 0}
							<div class="mt-4 grid gap-3 sm:grid-cols-2">
								{#each products as product, productIndex (`${product.product_page_url ?? product.title}-${productIndex}`)}
									<article class="flex flex-col justify-between gap-3 rounded-lg border p-4">
										<div>
											<h3 class="font-medium">{product.title ?? groceryItem.item}</h3>
											<p class="mt-1 text-sm text-muted-foreground">
												{#if getPrice(product) !== null}
													${getPrice(product)?.toFixed(2)} per item
												{:else}
													Price unavailable
												{/if}
											</p>
										</div>
										{#if product.product_page_url}
											<a
												href={product.product_page_url}
												target="_blank"
												rel="noopener noreferrer"
												class="inline-flex w-fit items-center rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
											>
												View at Walmart
											</a>
										{:else}
											<p class="text-sm text-muted-foreground">Product link unavailable</p>
										{/if}
									</article>
								{/each}
							</div>
						{:else}
							<p class="mt-3 text-sm text-muted-foreground">
								No Walmart products found for this ingredient.
							</p>
						{/if}
					</section>
				{/each}
			</div>
		{:else}
			<p class="rounded-xl border p-6 text-sm text-muted-foreground">
				This meal plan does not have a grocery list.
			</p>
		{/if}
	{:else}
		<p class="py-12 text-center text-sm text-muted-foreground">Loading shopping list...</p>
	{/if}
</main>