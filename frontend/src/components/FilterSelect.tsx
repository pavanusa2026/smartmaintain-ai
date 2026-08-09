import { FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';

interface Option {
  value: string;
  label: string;
}

interface FilterSelectProps {
  label: string;
  value: string;
  options: Option[];
  onChange: (value: string) => void;
  minWidth?: number;
}

/** Select filter defaulting visibly to "All" (value: all). */
export default function FilterSelect({ label, value, options, onChange, minWidth = 150 }: FilterSelectProps) {
  return (
    <FormControl size="small" sx={{ minWidth }}>
      <InputLabel id={`${label}-filter-label`}>{label}</InputLabel>
      <Select
        labelId={`${label}-filter-label`}
        value={value}
        label={label}
        onChange={(e: SelectChangeEvent) => onChange(e.target.value)}
        displayEmpty={false}
      >
        {options.map((opt) => (
          <MenuItem key={opt.value} value={opt.value}>
            {opt.label}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

export function filterValueToParam(value: string): string | undefined {
  return value === 'all' ? undefined : value;
}
