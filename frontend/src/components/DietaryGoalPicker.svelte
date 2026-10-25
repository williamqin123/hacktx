<script lang="ts">
    import { RadioGroup, RadioGroupItem } from '#lib/components/ui/radio-group';

    let { dietGoal = $bindable('maintain') } = $props();
</script>

<div class="space-y-1">
    <h2 class="text-lg font-medium">Diet Goal</h2>
    <p class="text-sm text-muted-foreground">
        Choose your primary goal.
    </p>
</div>

<RadioGroup bind:value={dietGoal} class="grid grid-cols-3 gap-3">
    {#each [
        { value: 'lose', label: 'Lose' },
        { value: 'maintain', label: 'Maintain' },
        { value: 'gain', label: 'Gain' }
    ] as mode}
        <label
            for={`goal-${mode.value}`}
            class="flex cursor-pointer flex-col items-center gap-2 rounded-lg border p-4 text-center transition-colors hover:bg-accent"
            class:border-primary={dietGoal === mode.value}
            class:bg-accent={dietGoal === mode.value}
        >
            <RadioGroupItem
                value={mode.value}
                id={`goal-${mode.value}`}
            />
            <span class="text-sm font-medium">{mode.label}</span>
        </label>
    {/each}
</RadioGroup>