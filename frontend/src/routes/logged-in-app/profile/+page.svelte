
<script lang="ts">
	import { Button } from '#lib/components/ui/button';
	import { Input } from '#lib/components/ui/input';
	import { Label } from '#lib/components/ui/label';
	import { Separator } from '#lib/components/ui/separator';

	let name = $state('');
	let age = $state<number | undefined>(undefined);
	let sex = $state('');
	let height = $state<number | undefined>(undefined);
	let weight = $state<number | undefined>(undefined);

	let dietaryRestrictions = $state<string[]>([]);
	let dietGoal = $state('maintain');
	import DietaryRestrictionsPicker from '#components/DietaryRestrictionsPicker.svelte';
	import DietaryGoalPicker from '#components/DietaryGoalPicker.svelte';

	import { apiFetch } from "#utils/api.js";

	let isSaving = $state(false);
	let errorMessage = $state('');
	let successMessage = $state('');

	async function saveProfile() {
		isSaving = true;
		errorMessage = '';
		successMessage = '';

		try {
			const profile = {
				name: name.trim(),
				age,
				sex,
				height,
				weight,
				dietaryRestrictions,
				goal: dietGoal
			};

			const response = await apiFetch(
				'http://localhost:5001/set-profile-info',
				{
					method: 'POST',
					headers: {
						'Content-Type': 'application/json'
					},
					body: JSON.stringify(profile)
				}
			);

			if (!response.ok) {
				throw new Error('Failed to save profile.');
			}

			successMessage = 'Profile saved successfully.';
		} catch (error) {
			errorMessage =
				error instanceof Error
					? error.message
					: 'Something went wrong.';
		} finally {
			isSaving = false;
		}
	}

	import { onMount } from 'svelte';

	async function loadProfile() {
		try {
			const response = await apiFetch(
				'http://localhost:5001/get-profile-info'
			);

			if (!response.ok) {
				throw new Error('Failed to load profile.');
			}

			const profile = await response.json();

			name = profile.name ?? '';
			age = profile.age ?? undefined;
			sex = profile.sex ?? '';
			height = profile.height ?? undefined;
			weight = profile.weight ?? undefined;
			dietaryRestrictions = profile.dietaryRestrictions ?? [];
			dietGoal = profile.goal ?? 'maintain';
		} catch (error) {
			errorMessage =
				error instanceof Error
					? error.message
					: 'Failed to load profile.';
		}
	}

	onMount(() => {
		loadProfile();
	});
</script>

<svelte:head>
	<title>My Profile</title>
	<meta
		name="description"
		content="Manage your personal details and dietary goals."
	/>
</svelte:head>

<div class="mx-auto w-full max-w-2xl space-y-8 px-4 py-8 sm:px-6">
	<header class="space-y-1">
		<h1 class="text-2xl font-semibold tracking-tight">My Profile</h1>
		<p class="text-sm text-muted-foreground">
			Manage your details, dietary preferences, and goals.
		</p>
	</header>

	<form
		onsubmit={(event) => {
			event.preventDefault();
			saveProfile();
		}}
		class="space-y-8"
	>
		<section class="space-y-4">
			<h2 class="text-lg font-medium">Personal Information</h2>

			<div class="space-y-2">
				<Label for="name">Name</Label>
				<Input
					id="name"
					bind:value={name}
					placeholder="Your name"
					required
				/>
			</div>

			<div class="grid grid-cols-2 gap-4">
				<div class="space-y-2">
					<Label for="age">Age</Label>
					<Input
						id="age"
						type="number"
						bind:value={age}
						min={1}
						max={120}
						placeholder="Years"
					/>
				</div>

				<div class="space-y-2">
					<Label for="sex">Sex</Label>
					<select
						id="sex"
						bind:value={sex}
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
					<Input
						id="height"
						type="number"
						bind:value={height}
						min={1}
						max={300}
						placeholder="e.g. 175"
					/>
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
						placeholder="e.g. 70"
					/>
				</div>
			</div>
		</section>

		<Separator />

		<section class="space-y-4">
			<DietaryRestrictionsPicker bind:value={dietaryRestrictions} />
		</section>

		<Separator />

		<section class="space-y-4">
			<DietaryGoalPicker bind:dietGoal={dietGoal} />
		</section>

		<div class="space-y-2">
			{#if errorMessage}
				<p class="text-sm text-destructive">{errorMessage}</p>
			{/if}

			{#if successMessage}
				<p class="text-sm text-green-600">{successMessage}</p>
			{/if}

			<div class="flex justify-end">
				<Button
					type="submit"
					class="w-full sm:w-auto"
					disabled={isSaving}
				>
					{isSaving ? 'Saving...' : 'Save Profile'}
				</Button>
			</div>
		</div>
	</form>
</div>
