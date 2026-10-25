<script lang="ts">
	import { Checkbox } from '#lib/components/ui/checkbox';

	type Props = {
		value?: string[];
	};

	let { value = $bindable([]) }: Props = $props();

	const dietaryOptions = [
		'Vegetarian',
		'Vegan',
		'Gluten-free',
		'Dairy-free',
		'Nut-free',
		'Pescatarian',
		'Halal',
		'Kosher'
	];

	function toggleRestriction(option: string, checked: boolean) {
		if (checked) {
			if (!value.includes(option)) {
				value = [...value, option];
			}
		} else {
			value = value.filter((item) => item !== option);
		}
	}
</script>


<div class="space-y-1">
    <h2 class="text-lg font-medium">Dietary Restrictions</h2>
    <p class="text-sm text-muted-foreground">
        Select all that apply.
    </p>
</div>

<div class="grid grid-cols-2 gap-4 sm:grid-cols-3">
    {#each dietaryOptions as option}
        <label
            for={`diet-${option}`}
            class="flex cursor-pointer items-center gap-2 text-sm"
        >
            <Checkbox
                id={`diet-${option}`}
                checked={value.includes(option)}
                onCheckedChange={(checked) =>
                    toggleRestriction(option, checked === true)}
            />
            <span>{option}</span>
        </label>
    {/each}
</div>
