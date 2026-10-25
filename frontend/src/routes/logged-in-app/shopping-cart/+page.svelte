<script lang="ts">
	import { onMount } from 'svelte';
	import { apiFetch } from '#utils/api.js';
	import { Button } from '#lib/components/ui/button';
	import { ShoppingCart, Trash2 } from '@lucide/svelte';

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

	let items = $state<CartItem[]>([]);
	let isLoading = $state(true);
	let errorMessage = $state('');
	let actionMessage = $state('');
	let isSaving = $state(false);

	onMount(() => {
		void loadCart();
	});

	async function loadCart() {
		isLoading = true;
		errorMessage = '';
		try {
			const response = await apiFetch('http://localhost:5001/api/cart');
			const result = await response.json();
			if (!response.ok) {
				throw new Error(result.error ?? 'Could not load your shopping cart.');
			}
			if (!Array.isArray(result.items)) {
				throw new Error('The shopping cart response was invalid.');
			}
			items = result.items;
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Could not load your shopping cart.';
		} finally {
			isLoading = false;
		}
	}

	async function saveItems(nextItems: CartItem[]) {
		isSaving = true;
		errorMessage = '';
		actionMessage = '';
		try {
			const response = await apiFetch('http://localhost:5001/api/cart', {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ items: nextItems })
			});
			const result = await response.json();
			if (!response.ok) {
				throw new Error(result.error ?? 'Could not update your shopping cart.');
			}
			if (!Array.isArray(result.items)) {
				throw new Error('The shopping cart response was invalid.');
			}
			items = result.items;
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Could not update your shopping cart.';
		} finally {
			isSaving = false;
		}
	}

	function updateQuantity(id: string, value: string) {
		const parsedQuantity = Number(value);
		const quantity = Number.isFinite(parsedQuantity)
			? Math.max(1, Math.min(99, Math.floor(parsedQuantity)))
			: 1;
		void saveItems(items.map((item) => item.id === id ? { ...item, quantity } : item));
	}

	function removeItem(id: string) {
		void saveItems(items.filter((item) => item.id !== id));
	}

	const total = $derived(
		items.reduce((sum, item) => sum + (item.price ?? 0) * item.quantity, 0)
	);
</script>

<svelte:head>
	<title>Shopping Cart</title>
	<meta name="description" content="Review and manage products saved to your shopping cart." />
</svelte:head>

<main class="mx-auto w-full max-w-5xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
	<header class="flex flex-wrap items-center justify-between gap-4">
		<div>
			<h1 class="text-3xl font-bold tracking-tight">Shopping Cart</h1>
			<p class="mt-2 text-muted-foreground">
				Products added from your meal plans and saved meals.
			</p>
		</div>
		<ShoppingCart class="size-7 text-primary" />
	</header>

	{#if errorMessage}
		<p class="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive" role="alert">
			{errorMessage}
		</p>
	{/if}
	{#if actionMessage}
		<p class="rounded-md border border-primary/20 bg-primary/5 p-3 text-sm" role="status">
			{actionMessage}
		</p>
	{/if}

	{#if isLoading}
		<p class="py-12 text-center text-sm text-muted-foreground" role="status">
			Loading shopping cart...
		</p>
	{:else if items.length === 0}
		<section class="rounded-xl border border-dashed p-8 text-center">
			<ShoppingCart class="mx-auto size-8 text-muted-foreground" />
			<h2 class="mt-3 font-semibold">Your cart is empty</h2>
			<p class="mt-2 text-sm text-muted-foreground">
				Add products from a meal plan's shopping list or from Saved Meals.
			</p>
			<Button class="mt-4" variant="outline" href="/logged-in-app/meal-plans">
				View meal plans
			</Button>
		</section>
	{:else}
		<section class="rounded-xl border bg-card p-5">
			<div class="divide-y">
				{#each items as item (item.id)}
					<article class="flex flex-wrap items-center gap-4 py-4 first:pt-0 last:pb-0">
						<div class="min-w-0 flex-1">
							<p class="font-medium">{item.title}</p>
							<p class="mt-1 text-sm text-muted-foreground">
								{item.ingredient} · For {item.meal_name}
								{#if item.retailer}
									· {item.retailer}
								{/if}
							</p>
							{#if item.product_page_url}
								<a
									class="mt-1 inline-block text-sm text-primary underline"
									href={item.product_page_url}
									target="_blank"
									rel="noopener noreferrer"
								>
									View product
								</a>
							{/if}
						</div>
						<div class="text-right text-sm">
							{#if item.price !== null}
								<p>${item.price.toFixed(2)} each</p>
								<p class="text-muted-foreground">
									Subtotal: ${(item.price * item.quantity).toFixed(2)}
								</p>
							{:else}
								<p class="text-muted-foreground">Price unavailable</p>
							{/if}
						</div>
						<label class="flex items-center gap-2 text-sm">
							<span class="sr-only">Quantity for {item.title}</span>
							<input
								type="number"
								min="1"
								max="99"
								step="1"
								value={item.quantity}
								disabled={isSaving}
								onchange={(event) => updateQuantity(item.id, event.currentTarget.value)}
								class="w-20 rounded-md border bg-background px-2 py-1.5"
							/>
						</label>
						<Button
							variant="ghost"
							size="icon"
							aria-label={`Remove ${item.title} from cart`}
							disabled={isSaving}
							onclick={() => removeItem(item.id)}
						>
							<Trash2 class="size-4 text-destructive" />
						</Button>
					</article>
				{/each}
			</div>
			<footer class="mt-5 flex flex-wrap items-center justify-between gap-3 border-t pt-4">
				<p class="text-lg font-semibold">Total: ${total.toFixed(2)}</p>
				<Button disabled={isSaving} onclick={() => actionMessage = 'Checkout is a demo and is not connected to a payment service.'}>
					Fake checkout
				</Button>
			</footer>
		</section>
	{/if}
</main>
