<script lang="ts">
	import { onMount } from 'svelte';
	import { Button } from '#lib/components/ui/button';
	import { Card } from '#lib/components/ui/card';
	import { Separator } from '#lib/components/ui/separator';
	import {
		BookOpen,
		CalendarDays,
		Clock3,
		Flame,
		ShoppingCart,
		UtensilsCrossed,
		Users,
		X
	} from '@lucide/svelte';
	import { apiFetch } from '#utils/api.js';

	type Meal = {
		name: string;
		estimated_calories_kcal_per_person: number;
		ingredients: string[];
		prep_time: number;
		Recipe: string[];
		shopping_list?: Array<{
			ingredient: string;
			quantity: string;
			products: Array<{
				title?: string;
				primary_offer?: { offer_price?: number | string };
				product_page_url?: string;
			}>;
		}>;
	};

	type MealPlan = {
		id: string;
		meal_plan: {
			days: number;
			people: number;
			diet?: string;
			daily_meals: Array<{
				day: number;
				meals: Record<string, Meal>;
			}>;
		};
		grocery_list: Array<{ item: string; quantity: string }>;
	};

	let mealPlans = $state<MealPlan[]>([]);
	let loading = $state(true);
	let error = $state('');
	let deleteError = $state('');
	let deletingPlanId = $state('');

	onMount(() => {
		loadMealPlans();
	});

	async function loadMealPlans() {
		loading = true;
		error = '';

		try {
			const response = await apiFetch('api/meal-plans');
			const result = await response.json();
			if (!response.ok) {
				throw new Error(result.error ?? 'Could not load saved meal plans.');
			}
			if (!Array.isArray(result.meal_plans)) {
				throw new Error('The response did not include a meal_plans list.');
			}
			mealPlans = result.meal_plans;
		} catch (loadError) {
			error =
				loadError instanceof Error
					? loadError.message
					: 'Could not load saved meal plans.';
		} finally {
			loading = false;
		}
	}

	function openShoppingList(id: string) {
		window.location.href = `/logged-in-app/meal-plans-shopping/${id}`;
	}

	async function deleteMealPlan(id: string) {
		deleteError = '';
		deletingPlanId = id;
		try {
			const response = await apiFetch(
				`http://localhost:5001/api/meal-plans/${encodeURIComponent(id)}`,
				{ method: 'DELETE' }
			);
			const result = await response.json();
			if (!response.ok) {
				throw new Error(result.error ?? 'Could not delete this meal plan.');
			}

			mealPlans = mealPlans.filter((plan) => plan.id !== id);
			sessionStorage.removeItem(`meal-plan-shopping:${id}`);
		} catch (requestError) {
			deleteError =
				requestError instanceof Error
					? requestError.message
					: 'Could not delete this meal plan.';
		} finally {
			deletingPlanId = '';
		}
	}
</script>

<svelte:head>
	<title>My Meal Plans</title>
	<meta name="description" content="Generated meal plans saved in the database." />
</svelte:head>

<div class="mx-auto flex h-full min-h-0 w-full max-w-5xl flex-col gap-6 p-4 sm:p-6">
	<header>
		<h1 class="text-2xl font-bold tracking-tight sm:text-3xl">My Meal Plans</h1>
		<p class="mt-1 text-sm text-muted-foreground">
			Each saved plan contains its days and meals.
		</p>
	</header>

	<Separator />

	{#if deleteError}
		<p class="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive" role="alert">
			{deleteError}
		</p>
	{/if}

	{#if loading}
		<p class="py-12 text-center text-sm text-muted-foreground">Loading meal plans...</p>
	{:else if error}
		<section class="flex flex-col items-start gap-3 rounded-xl border p-6" role="alert">
			<p class="text-sm text-destructive">{error}</p>
			<Button variant="outline" size="sm" onclick={loadMealPlans}>Try again</Button>
		</section>
	{:else if mealPlans.length === 0}
		<div class="flex min-h-64 flex-col items-center justify-center gap-3 rounded-xl border border-dashed p-8 text-center">
			<div class="rounded-full bg-muted p-4">
				<UtensilsCrossed class="size-7 text-muted-foreground" />
			</div>
			<h2 class="text-lg font-semibold">No meal plans yet</h2>
			<p class="max-w-sm text-sm text-muted-foreground">
				Generate a meal plan and it will appear here with all of its days and meals.
			</p>
			<Button href="/logged-in-app/studio">Generate a meal plan</Button>
		</div>
	{:else}
		<div class="flex items-center justify-between">
			<p class="text-sm text-muted-foreground">
				{mealPlans.length} saved {mealPlans.length === 1 ? 'meal plan' : 'meal plans'}
			</p>
			<Button variant="outline" size="sm" onclick={loadMealPlans}>Refresh</Button>
		</div>

		<div class="space-y-5">
			{#each mealPlans as plan (plan.id)}
				<Card class="relative space-y-5 p-5">
					<Button
						variant="ghost"
						size="icon"
						class="absolute right-3 top-3 size-8 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
						aria-label={`Delete ${plan.meal_plan.diet || 'meal plan'}`}
						title="Delete meal plan"
						disabled={Boolean(deletingPlanId)}
						onclick={() => deleteMealPlan(plan.id)}
					>
						<X class="size-4" />
					</Button>
					<header class="flex flex-wrap items-start justify-between gap-3 pr-10">
						<div>
							<h2 class="text-xl font-semibold">
								{plan.meal_plan.diet || 'Generated meal plan'}
							</h2>
							<div class="mt-2 flex flex-wrap gap-4 text-sm text-muted-foreground">
								<span class="inline-flex items-center gap-1.5">
									<CalendarDays class="size-4" />
									{plan.meal_plan.days} {plan.meal_plan.days === 1 ? 'day' : 'days'}
								</span>
								<span class="inline-flex items-center gap-1.5">
									<Users class="size-4" />
									{plan.meal_plan.people}
									{plan.meal_plan.people === 1 ? 'person' : 'people'}
								</span>
							</div>
						</div>
						<div class="flex flex-wrap gap-2">
							<Button
								variant="outline"
								size="sm"
								href={`/logged-in-app/meal-plan-recipes/${plan.id}`}
							>
								<BookOpen class="mr-2 size-4" />
								View Recipes
							</Button>
							<Button size="sm" onclick={() => openShoppingList(plan.id)}>
							<ShoppingCart class="mr-2 size-4" />
							Shopping List
							</Button>
						</div>
					</header>

					<div class="space-y-4">
						{#each plan.meal_plan.daily_meals as day (day.day)}
							<section class="rounded-lg border p-4">
								<h3 class="font-semibold">Day {day.day}</h3>
								<div class="mt-3 grid gap-3 md:grid-cols-3">
									{#each Object.entries(day.meals) as [mealType, meal] (mealType)}
										<article class="rounded-md bg-muted/40 p-3">
											<p class="text-xs font-semibold uppercase tracking-wide text-primary">
												{mealType}
											</p>
											<h4 class="mt-1 font-medium">{meal.name}</h4>
											<div class="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
												<span class="inline-flex items-center gap-1">
													<Flame class="size-3.5" />
													{meal.estimated_calories_kcal_per_person} kcal/person
												</span>
												<span class="inline-flex items-center gap-1">
													<Clock3 class="size-3.5" />
													{meal.prep_time} min
												</span>
											</div>
											<p class="mt-2 line-clamp-2 text-xs text-muted-foreground">
												{meal.ingredients.join(', ')}
											</p>
										</article>
									{/each}
								</div>
							</section>
						{/each}
					</div>
				</Card>
			{/each}
		</div>
	{/if}
</div>
