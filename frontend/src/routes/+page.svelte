
<script lang="ts">
    // @ts-ignore
  import { Button } from '#lib/components/ui/button';
  import { ArrowRight, ChefHat, Sparkles } from '@lucide/svelte';
</script>

<svelte:head>
  <title>Recipe Studio — Cook Something Great</title>
  <meta
    name="description"
    content="Discover personalized recipes made for you."
  />
</svelte:head>

<main class="min-h-screen bg-background text-foreground">
  <header class="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
    <a href="/" class="flex items-center gap-2 font-semibold tracking-tight">
      <span class="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
        <ChefHat class="size-5" />
      </span>
      <span class="text-lg">Recipe Studio</span>
    </a>

    <Button variant="outline" href="/login">
      Sign in <ArrowRight class="ml-2 size-4" />
    </Button>
  </header>

  <section class="mx-auto grid max-w-6xl items-center gap-12 px-6 py-16 md:grid-cols-2 md:py-28">
    <div class="space-y-7">
      <div class="inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm text-muted-foreground">
        <Sparkles class="size-4" />
        Your next favorite meal starts here
      </div>

      <h1 class="max-w-xl text-5xl font-bold tracking-tight sm:text-6xl">
        Make something
        <span class="text-primary">delicious.</span>
      </h1>

      <p class="max-w-lg text-lg leading-8 text-muted-foreground">
        Turn your ingredients, cravings, and dietary preferences into
        recipes worth making. Your next great meal is only a few clicks away.
      </p>

      <div class="flex flex-col gap-3 sm:flex-row">
        <Button size="lg" href="/login" class="h-12 px-6">
          Get started <ArrowRight class="ml-2 size-4" />
        </Button>
      </div>

      <p class="text-sm text-muted-foreground">
        Sign in to start creating your own recipes.
      </p>
    </div>

    <div class="relative">
      <div class="absolute -inset-4 rounded-3xl bg-primary/5 blur-2xl"></div>
      <div class="relative overflow-hidden rounded-3xl border bg-card p-3 shadow-sm">
        <img
          src="https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=1200&q=85"
          alt="Freshly prepared meal with colorful vegetables"
          class="aspect-[4/5] w-full rounded-2xl object-cover md:aspect-[4/4.5]"
        />
        <div class="absolute inset-x-6 bottom-6 rounded-2xl border bg-background/95 p-4 backdrop-blur">
          <p class="text-sm text-muted-foreground">A little inspiration</p>
          <p class="mt-1 font-semibold">Fresh ingredients. Endless possibilities.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="mx-auto max-w-6xl px-6 pb-20">
    <div class="grid gap-4 sm:grid-cols-3">
      <div class="rounded-2xl border p-5">
        <ChefHat class="mb-4 size-5 text-primary" />
        <h2 class="font-semibold">Personalized recipes</h2>
        <p class="mt-2 text-sm leading-6 text-muted-foreground">
          Find meals that match your tastes and preferences.
        </p>
      </div>

      <div class="rounded-2xl border p-5">
        <Sparkles class="mb-4 size-5 text-primary" />
        <h2 class="font-semibold">AI-powered inspiration</h2>
        <p class="mt-2 text-sm leading-6 text-muted-foreground">
          Turn a few ideas into your next kitchen creation.
        </p>
      </div>

      <div class="rounded-2xl border p-5">
        <ArrowRight class="mb-4 size-5 text-primary" />
        <h2 class="font-semibold">Simple to get started</h2>
        <p class="mt-2 text-sm leading-6 text-muted-foreground">
          Sign in and start building your next recipe.
        </p>
      </div>
    </div>
  </section>
</main>
