<script lang="ts">
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { apiFetch } from '#utils/api.js';
	import { Button } from '#lib/components/ui/button';
	import { ShoppingCart } from '@lucide/svelte';

	type GroceryItem = {
		item: string;
		quantity?: string;
	};

	type WalmartProduct = {
		product_id?: string | number;
		title?: string;
		primary_offer?: {
			offer_price?: number | string;
		};
		product_page_url?: string;
	};

	type KrogerProduct = {
		upc: string;
		description?: string;
		brand?: string;
		price: number;
		size?: string;
		product_url?: string;
		pickup_available: boolean;
	};

	type ShoppingProduct = {
		id: string;
		title: string;
		price: number | null;
		url?: string;
		upc?: string;
		brand?: string;
		size?: string;
		retailer: 'Walmart' | 'Kroger';
	};

	type CartItem = {
		id: string;
		title: string;
		meal_name: string;
		ingredient: string;
		quantity: number;
		price: number | null;
		product_page_url?: string;
		upc?: string;
		retailer?: 'Walmart' | 'Kroger';
	};

	type KrogerLocation = {
		location_id: string;
		name: string;
		address: string;
		distance?: number;
	};

	type Meal = {
		name?: string;
		ingredients?: string[];
	};

	type MealPlan = {
		meal_plan?: {
			days?: number;
			people?: number;
			daily_meals?: Array<{
				day?: number;
				meals?: Record<string, Meal>;
			}>;
		};
		grocery_list?: GroceryItem[];
		walmart_results?: ShoppingData['walmartResults'];
	};

	type ShoppingData = {
		mealPlan: MealPlan;
		walmartResults: Record<string, { organic_results?: WalmartProduct[] }>;
		krogerProducts?: Record<string, KrogerProduct[]>;
		krogerLocation?: KrogerLocation;
	};

	let shoppingData = $state<ShoppingData | null>(null);
	let selectedRetailer = $state<'Walmart' | 'Kroger'>('Walmart');
	let loadError = $state('');
	let krogerError = $state('');
	let isPlaceholder = $state(false);
	let isLoadingProducts = $state(false);
	let hasLoadedKrogerProducts = $state(false);
	let productQuantities = $state<Record<string, number>>({});
	let cartItems = $state<CartItem[]>([]);
	let cartError = $state('');
	let cartMessage = $state('');
	let isCartReady = $state(false);
	let isAddingAll = $state(false);

	onMount(() => {
		void loadShoppingData();
		void loadCart();
	});

	async function loadShoppingData() {
		const slug = page.params.slug ?? '';
		const storedData = sessionStorage.getItem(`meal-plan-shopping:${slug}`);
		if (!storedData) {
			await loadSavedMealPlanShoppingList(slug);
			return;
		}

		try {
			const stored = JSON.parse(storedData) as {
				mealPlan?: MealPlan;
				walmartResults?: ShoppingData['walmartResults'];
			};
			if (!stored.mealPlan) {
				throw new Error('The saved shopping list is missing its meal plan.');
			}
			shoppingData = {
				mealPlan: stored.mealPlan,
				walmartResults:
					stored.walmartResults ?? stored.mealPlan.walmart_results ?? {}
			};
		} catch {
			loadError = 'The saved shopping list could not be read. Generate a new meal plan to try again.';
		}
	}

	async function chooseRetailer(retailer: 'Walmart' | 'Kroger') {
		selectedRetailer = retailer;
		if (retailer === 'Kroger' && !hasLoadedKrogerProducts && !isLoadingProducts) {
			await loadKrogerProducts();
		}
	}

	async function loadKrogerProducts() {
		const items = shoppingData?.mealPlan.grocery_list?.map((item) => item.item) ?? [];
		if (items.length === 0 || !shoppingData) return;

		isLoadingProducts = true;
		krogerError = '';
		try {
			const response = await apiFetch('api/kroger/products', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ items })
			});
			const result = await response.json();
			if (!response.ok) {
				throw new Error(result.error ?? 'Could not load Kroger pickup products.');
			}
			if (
				!result.products ||
				typeof result.products !== 'object' ||
				!result.location
			) {
				throw new Error('The Kroger products response was invalid.');
			}
			shoppingData = {
				...shoppingData,
				krogerProducts: result.products,
				krogerLocation: result.location
			};
			hasLoadedKrogerProducts = true;
		} catch (error) {
			krogerError =
				error instanceof Error
					? error.message
					: 'Kroger pickup products are unavailable.';
		} finally {
			isLoadingProducts = false;
		}
	}

	async function loadSavedMealPlanShoppingList(mealPlanId: string) {
		try {
			const response = await apiFetch('api/meal-plans');
			const result = await response.json();
			if (!response.ok) {
				throw new Error(result.error ?? 'Could not load the saved meal plan.');
			}

			const mealPlan = result.meal_plans?.find(
				(savedPlan: { id?: string }) => savedPlan.id === mealPlanId
			);
			if (!mealPlan || !mealPlan.meal_plan || !Array.isArray(mealPlan.grocery_list)) {
				isPlaceholder = true;
				return;
			}

			shoppingData = {
				mealPlan: {
					meal_plan: mealPlan.meal_plan,
					grocery_list: mealPlan.grocery_list
				},
				walmartResults: mealPlan.walmart_results ?? {},
				krogerProducts: {}
			};
		} catch (error) {
			loadError =
				error instanceof Error
					? error.message
					: 'Could not load the saved meal plan shopping list.';
		}
	}

	function formatSlug(slug: string) {
		return slug
			.split('-')
			.map((word) => word.charAt(0).toUpperCase() + word.slice(1))
			.join(' ');
	}

	function walmartResultKey(groceryItem: GroceryItem) {
		const itemName = groceryItem.item.trim();
		const quantity = groceryItem.quantity?.trim() ?? '';
		return quantity && !itemName.toLocaleLowerCase().includes(quantity.toLocaleLowerCase())
			? `${quantity} ${itemName}`
			: quantity || itemName;
	}

	function getProducts(groceryItem: GroceryItem): ShoppingProduct[] {
		if (selectedRetailer === 'Walmart') {
			const products =
				shoppingData?.walmartResults?.[walmartResultKey(groceryItem)]?.organic_results ?? [];
			return products
				.map((product, index) => {
					const price = Number(product.primary_offer?.offer_price);
					return {
						id: String(product.product_id ?? product.product_page_url ?? `${groceryItem.item}-${index}`),
						title: product.title ?? groceryItem.item,
						price: Number.isFinite(price) ? price : null,
						url: product.product_page_url,
						retailer: 'Walmart' as const
					};
				})
				.sort((first, second) => {
					if (first.price === null) return second.price === null ? 0 : 1;
					if (second.price === null) return -1;
					return first.price - second.price;
				});
		}

		return [...(shoppingData?.krogerProducts?.[groceryItem.item] ?? [])]
			.map((product) => ({
				id: product.upc,
				title: product.description ?? groceryItem.item,
				price: product.price,
				url: product.product_url,
				upc: product.upc,
				brand: product.brand,
				size: product.size,
				retailer: 'Kroger' as const
			}))
			.sort((first, second) => (first.price ?? Infinity) - (second.price ?? Infinity));
	}

	function productKey(groceryItem: GroceryItem, product: ShoppingProduct) {
		return `${product.retailer}:${groceryItem.item}:${product.id}`;
	}

	function getMealsForItem(groceryItem: GroceryItem) {
		const item = normalizeText(groceryItem.item);
		if (!item) return [];

		return (shoppingData?.mealPlan.meal_plan?.daily_meals ?? []).flatMap((day) =>
			Object.entries(day.meals ?? {})
				.filter(([, meal]) =>
					(meal.ingredients ?? []).some((ingredient) => {
						const normalizedIngredient = normalizeText(ingredient);
						return (
							normalizedIngredient.includes(item) ||
							item.includes(normalizedIngredient)
						);
					})
				)
				.map(([mealType, meal]) =>
					`${day.day ? `Day ${day.day} ` : ''}${mealType}: ${meal.name ?? 'Meal'}`
				)
		);
	}

	function normalizeText(value: string) {
		return value.toLocaleLowerCase().replace(/[^a-z0-9]/g, '');
	}

	async function loadCart() {
		try {
			const response = await apiFetch('api/cart');
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

	async function addItemsToCart(itemsToAdd: CartItem[]) {
		if (itemsToAdd.length === 0) {
			throw new Error(`No priced ${selectedRetailer} products were found for this shopping list.`);
		}

		const nextItems = [...cartItems];
		for (const item of itemsToAdd) {
			const existing = nextItems.find((cartItem) => cartItem.id === item.id);
			if (existing) {
				existing.quantity = Math.min(99, existing.quantity + item.quantity);
			} else {
				nextItems.push(item);
			}
		}

		const response = await apiFetch('api/cart', {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ items: nextItems })
		});
		const result = await response.json();
		if (!response.ok) {
			throw new Error(result.error ?? 'Could not add products to your cart.');
		}
		cartItems = result.items;
		cartError = '';
	}

	function cheapestCartItems() {
		const planId = page.params.slug ?? '';
		return (shoppingData?.mealPlan.grocery_list ?? []).flatMap((groceryItem) => {
			const product = getProducts(groceryItem).find((candidate) => candidate.price !== null);
			if (!product) return [];
			const price = product.price;
			if (price === null) return [];
			const productUrl = product.url;
			return [{
				id: `${planId}:${selectedRetailer}:${groceryItem.item}:${product.id}`,
				title: product.title,
				meal_name: getMealsForItem(groceryItem).join(', ') || 'Meal plan',
				ingredient: groceryItem.item,
				quantity: 1,
				price,
				product_page_url: productUrl,
				upc: product.upc,
				retailer: selectedRetailer
			} satisfies CartItem];
		});
	}

	async function addShoppingListToCart() {
		isAddingAll = true;
		cartError = '';
		cartMessage = '';
		try {
			const itemsToAdd = cheapestCartItems();
			await addItemsToCart(itemsToAdd);
			cartMessage = `Added all ${itemsToAdd.length} available products to your cart.`;
		} catch (error) {
			cartError = error instanceof Error ? error.message : 'Could not add the shopping list to your cart.';
		} finally {
			isAddingAll = false;
		}
	}

	const selectedItems = $derived.by(() => {
		const items: Array<{ id: string; title: string; price: number; quantity: number }> = [];
		for (const groceryItem of shoppingData?.mealPlan.grocery_list ?? []) {
			for (const product of getProducts(groceryItem)) {
				const id = productKey(groceryItem, product);
				const quantity = productQuantities[id] ?? 0;
				const price = product.price;
				if (quantity > 0 && price !== null) {
					items.push({
						id,
						title: product.title,
						price,
						quantity
					});
				}
			}
		}
		return items;
	});
	const cartTotal = $derived(
		selectedItems.reduce((total, item) => total + item.price * item.quantity, 0)
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
		content="Compare Walmart and Kroger products, prices, and local pickup availability for your meal plan ingredients."
	/>
</svelte:head>

<main class="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
	<header class="mb-8">
		<div class="flex flex-wrap items-start justify-between gap-4">
			<div>
				<p class="text-sm font-semibold uppercase tracking-wide text-primary">Meal plan</p>
				<h1 class="mt-2 text-3xl font-bold tracking-tight">Shopping list</h1>
				<p class="mt-2 text-muted-foreground">
					Compare ingredient options from Walmart and your nearest Kroger.
				</p>
			</div>
			<Button variant="outline" href={`/logged-in-app/meal-plan-recipes/${page.params.slug}`}>
				View Recipes
			</Button>
		</div>
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
	{:else if isPlaceholder}
		<section class="rounded-xl border border-dashed bg-card p-8 text-center">
			<h2 class="text-xl font-semibold">
				{formatSlug(page.params.slug ?? 'meal-plan')}
			</h2>
			<p class="mx-auto mt-2 max-w-lg text-sm text-muted-foreground">
				This meal plan's shopping list will appear here once its ingredients and product links are connected.
			</p>
			<a
				href="/logged-in-app/meal-plans"
				class="mt-5 inline-flex rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted"
			>
				Back to meal plans
			</a>
		</section>
	{:else if shoppingData}
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
		{#if selectedRetailer === 'Kroger' && isLoadingProducts}
			<p class="mb-4 rounded-md border p-3 text-sm text-muted-foreground" role="status">
				Checking prices and pickup availability at your nearest Kroger...
			</p>
		{:else if selectedRetailer === 'Kroger' && shoppingData.krogerLocation}
			<p class="mb-4 rounded-md border bg-muted/30 p-3 text-sm">
				Pickup store: <strong>{shoppingData.krogerLocation.name}</strong>
				{#if shoppingData.krogerLocation.address}
					<span class="text-muted-foreground"> — {shoppingData.krogerLocation.address}</span>
				{/if}
				{#if shoppingData.krogerLocation.distance !== undefined}
					<span class="text-muted-foreground">
						({shoppingData.krogerLocation.distance} miles away)
					</span>
				{/if}
			</p>
		{/if}
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

		{#if shoppingData.mealPlan.grocery_list?.length}
			<div class="mb-5 flex flex-wrap items-center gap-2">
				<span class="mr-2 text-sm font-medium">Shop at:</span>
				<Button
					variant={selectedRetailer === 'Walmart' ? 'default' : 'outline'}
					aria-pressed={selectedRetailer === 'Walmart'}
					onclick={() => chooseRetailer('Walmart')}
				>
					Walmart
				</Button>
				<Button
					variant={selectedRetailer === 'Kroger' ? 'default' : 'outline'}
					aria-pressed={selectedRetailer === 'Kroger'}
					onclick={() => chooseRetailer('Kroger')}
				>
					Kroger
				</Button>
			</div>
			{#if selectedRetailer === 'Kroger' && krogerError}
				<p class="mb-4 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive" role="alert">
					{krogerError}
				</p>
			{/if}
			<div class="mb-4 flex justify-end">
				<Button onclick={addShoppingListToCart} disabled={isAddingAll || (selectedRetailer === 'Kroger' && isLoadingProducts) || !isCartReady || Boolean(cartError) || (selectedRetailer === 'Kroger' && Boolean(krogerError))}>
					<ShoppingCart class="mr-2 size-4" />
					{isAddingAll ? 'Adding all...' : 'Add all to cart'}
				</Button>
			</div>
			<div class="space-y-3">
				{#each shoppingData.mealPlan.grocery_list as groceryItem, index (`${groceryItem.item}-${index}`)}
					{@const products = getProducts(groceryItem)}
					<details class="rounded-xl border bg-card">
						<summary class="flex cursor-pointer list-inside flex-wrap items-center justify-between gap-2 px-5 py-4">
							<div>
								<span class="font-semibold">{groceryItem.item}</span>
								{#each getMealsForItem(groceryItem) as mealName, mealIndex (`${mealName}-${mealIndex}`)}
									<span class="ml-2 inline-flex rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
										{mealName}
									</span>
								{/each}
							</div>
							<span class="text-sm text-muted-foreground">
								{groceryItem.quantity || 'Quantity not specified'}
							</span>
						</summary>
						<div class="border-t p-4">
							{#if products.length > 0}
								<div class="flex flex-col">
									{#each products as product, productIndex (`${product.id}-${productIndex}`)}
										{@const price = product.price}
										<article class="flex flex-wrap items-center justify-between gap-4 border-b py-4 last:border-b-0">
											<div class="min-w-0 flex-1">
										<h3 class="font-medium">{product.title}</h3>
												<p class="mt-1 text-sm text-muted-foreground">
													{#if price !== null}
														${price.toFixed(2)}{product.size ? ` · ${product.size}` : ''}
													{:else}
														Price unavailable
													{/if}
													{#if product.brand}
														<span> · {product.brand}</span>
													{/if}
												</p>
												{#if product.retailer === 'Kroger'}
													<p class="mt-1 text-xs text-green-700">
														In stock for curbside pickup at this store
													</p>
												{/if}
											{#if product.url}
												<a
													href={product.url}
													target="_blank"
													rel="noopener noreferrer"
													class="mt-1 inline-block text-sm text-primary underline"
												>
													View at {product.retailer}
												</a>
												{/if}
											</div>
											<label class="flex items-center gap-2 text-sm">
												<span class="sr-only">Quantity to add for {product.title}</span>
												<input
													type="number"
													min="0"
													max="99"
													step="1"
													value={productQuantities[productKey(groceryItem, product)] ?? 0}
													oninput={(event) => {
														const value = Number(event.currentTarget.value);
														const key = productKey(groceryItem, product);
														productQuantities = {
															...productQuantities,
															[key]: Number.isFinite(value)
																? Math.max(0, Math.min(99, Math.floor(value)))
																: 0
														};
													}}
													class="w-16 rounded-md border bg-background px-2 py-1.5"
												/>
											</label>
											<p class="min-w-20 text-right text-sm font-semibold">
												${((price ?? 0) * (productQuantities[productKey(groceryItem, product)] ?? 0)).toFixed(2)}
											</p>
										</article>
									{/each}
								</div>
							{:else}
								<p class="text-sm text-muted-foreground">
									No {selectedRetailer} products were found for this ingredient.
								</p>
							{/if}
						</div>
					</details>
				{/each}
			</div>
		{:else}
			<p class="rounded-xl border p-6 text-sm text-muted-foreground">
				This meal plan does not have a grocery list.
			</p>
		{/if}

		<section class="sticky bottom-4 z-10 mt-6 flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-background/95 p-4 shadow-lg backdrop-blur">
			<p class="text-lg font-semibold">Total: ${cartTotal.toFixed(2)}</p>
			<Button>
				Fake checkout
			</Button>
		</section>
	{:else}
		<p class="py-12 text-center text-sm text-muted-foreground">Loading shopping list...</p>
	{/if}
</main>