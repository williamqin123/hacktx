
<script lang="ts">
    import { Button } from '#lib/components/ui/button';
    import { Card } from '#lib/components/ui/card';
    import { Badge } from '#lib/components/ui/badge';
    import { Separator } from '#lib/components/ui/separator';
    import {
        Trash2,
        ShoppingCart,
        CalendarDays,
        Users,
        UtensilsCrossed,
        Plus
    } from '@lucide/svelte';

    type MealPlan = {
        id: string;
        slug: string;
        name: string;
        days: number;
        people: number;
        image: string;
    };

    let mealPlans = $state<MealPlan[]>([
        {
            id: '1',
            slug: 'healthy-mediterranean-week',
            name: 'Healthy Mediterranean Week',
            days: 7,
            people: 2,
            image: 'https://images.unsplash.com/photo-1547592180-85f173990554?w=400&h=300&fit=crop'
        },
        {
            id: '2',
            slug: 'high-protein-meal-prep',
            name: 'High Protein Meal Prep',
            days: 5,
            people: 1,
            image: 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop'
        },
        {
            id: '3',
            slug: 'family-dinner-plan',
            name: 'Family Dinner Plan',
            days: 7,
            people: 4,
            image: 'https://images.unsplash.com/photo-1547592180-85f173990554?w=400&h=300&fit=crop'
        },
        {
            id: '4',
            slug: 'quick-and-easy-meals',
            name: 'Quick and Easy Meals',
            days: 3,
            people: 2,
            image: 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop'
        },
        {
            id: '5',
            slug: 'budget-friendly-weekly-plan',
            name: 'Budget-Friendly Weekly Plan',
            days: 7,
            people: 3,
            image: 'https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=400&h=300&fit=crop'
        }
    ]);

    function deleteMealPlan(id: string) {
        mealPlans = mealPlans.filter((plan) => plan.id !== id);
    }

    function openMealPlan(slug: string) {
        window.location.href = `/meal-plans/${slug}`;
    }

    function openShoppingList(slug: string) {
        window.location.href = `/meal-plans/${slug}/shopping-list`;
    }
</script>

<svelte:head>
    <title>My Meal Plans</title>
    <meta
        name="description"
        content="View and manage your saved meal plans."
    />
</svelte:head>

<div class="mx-auto flex h-full min-h-0 w-full max-w-5xl flex-col gap-6 p-4 sm:p-6">
    <div>
        <h1 class="text-2xl font-bold tracking-tight sm:text-3xl">
            My Meal Plans
        </h1>
        <p class="mt-1 text-sm text-muted-foreground">
            Manage your meal plans and shopping lists.
        </p>
    </div>

    <Separator />

    <p class="text-sm text-muted-foreground">
        {mealPlans.length} {mealPlans.length === 1 ? 'meal plan' : 'meal plans'}
    </p>

    <div class="min-h-0 flex-1 overflow-y-auto">
        {#if mealPlans.length === 0}
            <div class="flex min-h-64 flex-col items-center justify-center gap-3 rounded-xl border border-dashed p-8 text-center">
                <div class="rounded-full bg-muted p-4">
                    <UtensilsCrossed class="size-7 text-muted-foreground" />
                </div>
                <h2 class="text-lg font-semibold">No meal plans yet</h2>
                <p class="max-w-sm text-sm text-muted-foreground">
                    Your meal plans will appear here once you create them.
                </p>
            </div>
        {:else}
            <div class="flex flex-col gap-3 pb-4">
                {#each mealPlans as plan (plan.id)}
                    <Card
                        class="cursor-pointer overflow-hidden p-0 transition-colors hover:bg-muted/50"
                    >
                        <div
                            role="link"
                            tabindex="0"
                            aria-label={`Open ${plan.name}`}
                            class="flex min-w-0 items-center gap-3 p-3 sm:gap-5 sm:p-4"
                            onclick={() => openMealPlan(plan.slug)}
                            onkeydown={(event) => {
                                if (event.target !== event.currentTarget) return;
                                if (event.key === 'Enter' || event.key === ' ') {
                                    event.preventDefault();
                                    openMealPlan(plan.slug);
                                }
                            }}
                        >
                            <img
                                src={plan.image}
                                alt={plan.name}
                                class="size-20 shrink-0 rounded-lg object-cover sm:size-28"
                                loading="lazy"
                            />

                            <div class="min-w-0 flex-1">
                                <h2 class="truncate text-sm font-semibold sm:text-base">
                                    {plan.name}
                                </h2>

                                <div class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2 text-xs text-muted-foreground sm:gap-x-4 sm:text-sm">
                                    <span class="inline-flex items-center gap-1.5">
                                        <CalendarDays class="size-4 shrink-0" />
                                        {plan.days} {plan.days === 1 ? 'day' : 'days'}
                                    </span>

                                    <span class="inline-flex items-center gap-1.5">
                                        <Users class="size-4 shrink-0" />
                                        {plan.people} {plan.people === 1 ? 'person' : 'people'}
                                    </span>
                                </div>

                                <div
                                    class="mt-3 flex flex-wrap items-center gap-2"
                                    onclick={(event) => event.stopPropagation()}
                                    onkeydown={(event) => event.stopPropagation()}
                                >
                                    <Button
                                        size="sm"
                                        onclick={() => openShoppingList(plan.slug)}
                                    >
                                        <ShoppingCart class="mr-2 size-4" />
                                        Shopping List
                                    </Button>

                                    <Button
                                        size="icon"
                                        variant="outline"
                                        class="size-9 text-destructive hover:bg-destructive hover:text-destructive-foreground"
                                        aria-label={`Delete ${plan.name}`}
                                        title="Delete meal plan"
                                        onclick={() => deleteMealPlan(plan.id)}
                                    >
                                        <Trash2 class="size-4" />
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </Card>
                {/each}
            </div>
        {/if}
    </div>
</div>
