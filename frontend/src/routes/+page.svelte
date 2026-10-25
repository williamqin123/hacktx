<script lang="ts">
	import { ArrowRight, ChefHat } from '@lucide/svelte';
	import { Button } from '#lib/components/ui/button';
	import { Input } from '#lib/components/ui/input';
	import { Label } from '#lib/components/ui/label';
	import { Separator } from '#lib/components/ui/separator';
	import DietaryRestrictionsPicker from '#components/DietaryRestrictionsPicker.svelte';
	import DietaryGoalPicker from '#components/DietaryGoalPicker.svelte';

	const onboardingProfileKey = 'pending-onboarding-profile';

	let name = $state('');
	let age = $state<number | undefined>();
	let sex = $state('');
	let height = $state<number | undefined>();
	let weight = $state<number | undefined>();
	let activityLevel = $state('sedentary');
	let dislikes = $state('');
	let dietaryRestrictions = $state<string[]>([]);
	let goal = $state('maintain');
	let errorMessage = $state('');

	function continueToLogin(event: SubmitEvent) {
		event.preventDefault();
		errorMessage = '';

		if (age === undefined || !Number.isInteger(age) || age < 1 || age > 120) {
			errorMessage = 'Enter an age between 1 and 120.';
			return;
		}
		if (!sex) {
			errorMessage = 'Select an option for sex.';
			return;
		}
		if (!height || height < 1 || height > 300) {
			errorMessage = 'Enter a height between 1 and 300 cm.';
			return;
		}
		if (!weight || weight < 1 || weight > 700) {
			errorMessage = 'Enter a weight between 1 and 700 kg.';
			return;
		}

		sessionStorage.setItem(
			onboardingProfileKey,
			JSON.stringify({
				name: name.trim(),
				age,
				sex,
				height,
				weight,
				activityLevel,
				dislikes: dislikes.trim(),
				dietaryRestrictions,
				goal
			})
		);
		window.location.assign('/login');
	}
</script>

<svelte:head>
	<title>Set up your profile — Recipe Studio</title>
	<meta
		name="description"
		content="Set your profile and food preferences before creating personalized meal plans."
	/>
</svelte:head>

<main class="min-h-screen bg-muted/30 px-4 py-8 sm:py-12">
	<div class="mx-auto w-full max-w-2xl space-y-8 rounded-2xl border bg-background p-5 shadow-sm sm:p-8">
		<header class="space-y-3 text-center">
			<div class="mx-auto flex size-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
				<ChefHat class="size-6" />
			</div>
			<p class="text-sm font-semibold uppercase tracking-wide text-primary">Recipe Studio setup</p>
			<h1 class="text-3xl font-bold tracking-tight">Let’s personalize your meals</h1>
			<p class="text-sm text-muted-foreground">
				First tell us about yourself and your food preferences. Then sign in to save them to your account.
			</p>
		</header>

		<form onsubmit={continueToLogin} class="space-y-8">
			<section class="space-y-4">
				<h2 class="text-lg font-semibold">Your profile</h2>
				<div class="space-y-2">
					<Label for="name">Name</Label>
					<Input id="name" bind:value={name} placeholder="Your name" />
				</div>

				<div class="grid gap-4 sm:grid-cols-2">
					<div class="space-y-2">
						<Label for="age">Age</Label>
						<Input id="age" type="number" bind:value={age} min={1} max={120} required />
					</div>
					<div class="space-y-2">
						<Label for="sex">Sex</Label>
						<select
							id="sex"
							bind:value={sex}
							required
							class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
						>
							<option value="">Select</option>
							<option value="female">Female</option>
							<option value="male">Male</option>
							<option value="intersex">Intersex</option>
							<option value="other">Other</option>
							<option value="prefer_not_to_say">Prefer not to say</option>
						</select>
					</div>
					<div class="space-y-2">
						<Label for="height">Height (cm)</Label>
						<Input id="height" type="number" bind:value={height} min={1} max={300} required />
					</div>
					<div class="space-y-2">
						<Label for="weight">Weight (kg)</Label>
						<Input
							id="weight"
							type="number"
							bind:value={weight}
							min={1}
							max={700}
							step="0.1"
							required
						/>
					</div>
				</div>

				<div class="space-y-2">
					<Label for="activity-level">Activity level</Label>
					<select
						id="activity-level"
						bind:value={activityLevel}
						class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
					>
						<option value="sedentary">Sedentary — little or no exercise</option>
						<option value="lightly_active">Lightly active — exercise 1–3 days/week</option>
						<option value="moderately_active">Moderately active — exercise 3–5 days/week</option>
						<option value="very_active">Very active — exercise 6–7 days/week</option>
						<option value="extra_active">Extremely active — intense exercise or physical job</option>
					</select>
				</div>
			</section>

			<Separator />

			<section class="space-y-4">
				<div class="space-y-2">
					<Label for="dislikes">Foods you dislike</Label>
					<textarea
						id="dislikes"
						bind:value={dislikes}
						placeholder="e.g. mushrooms, olives, cilantro"
						rows={3}
						class="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
					></textarea>
				</div>
				<DietaryRestrictionsPicker bind:value={dietaryRestrictions} />
			</section>

			<Separator />

			<DietaryGoalPicker bind:dietGoal={goal} />

			{#if errorMessage}
				<p class="text-sm text-destructive" role="alert">{errorMessage}</p>
			{/if}

			<Button type="submit" class="w-full">
				Continue to sign in <ArrowRight class="ml-2 size-4" />
			</Button>
		</form>
	</div>
</main>
