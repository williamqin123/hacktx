
<script lang="ts">
	import { Button } from '#lib/components/ui/button';
	import { Input } from '#lib/components/ui/input';
	import { Label } from '#lib/components/ui/label';
	import { Checkbox } from '#lib/components/ui/checkbox';
	import { RadioGroup, RadioGroupItem } from '#lib/components/ui/radio-group';
	import { Separator } from '#lib/components/ui/separator';

	let name = $state('');
	let age = $state<number | undefined>(undefined);
	let sex = $state('');
	let height = $state<number | undefined>(undefined);
	let weight = $state<number | undefined>(undefined);

	let restrictions = $state<string[]>([]);
	let goal = $state('maintain');

	import DietaryRestrictionsPicker from '#components/DietaryRestrictionsPicker.svelte';

	function saveProfile() {
		const profile = {
			name,
			age,
			sex,
			height,
			weight,
			dietary_restrictions: restrictions,
			goal
		};

		// Replace with your API request.
		console.log('Saving profile:', profile);
	}
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
			<DietaryRestrictionsPicker bind:value={restrictions} />
		</section>

		<Separator />

		<section class="space-y-4">
			<div class="space-y-1">
				<h2 class="text-lg font-medium">Diet Goal</h2>
				<p class="text-sm text-muted-foreground">
					Choose your primary goal.
				</p>
			</div>

			<RadioGroup bind:value={goal} class="grid grid-cols-3 gap-3">
				{#each [
					{ value: 'lose', label: 'Lose' },
					{ value: 'maintain', label: 'Maintain' },
					{ value: 'gain', label: 'Gain' }
				] as mode}
					<label
						for={`goal-${mode.value}`}
						class="flex cursor-pointer flex-col items-center gap-2 rounded-lg border p-4 text-center transition-colors hover:bg-accent"
						class:border-primary={goal === mode.value}
						class:bg-accent={goal === mode.value}
					>
						<RadioGroupItem
							value={mode.value}
							id={`goal-${mode.value}`}
						/>
						<span class="text-sm font-medium">{mode.label}</span>
					</label>
				{/each}
			</RadioGroup>
		</section>

		<div class="flex justify-end">
			<Button type="submit" class="w-full sm:w-auto">
				Save Profile
			</Button>
		</div>
	</form>
</div>
