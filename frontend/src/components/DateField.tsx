import { TextField } from '@mui/material';
import type { TextFieldProps } from '@mui/material';

/** Date input without browser placeholder overlapping the MUI label. */
export default function DateField({ value, onChange, label, sx, ...rest }: TextFieldProps) {
  const hasValue = Boolean(value);

  return (
    <TextField
      fullWidth
      label={label}
      type="date"
      value={value ?? ''}
      onChange={onChange}
      margin="normal"
      slotProps={{
        inputLabel: { shrink: true },
        htmlInput: {
          placeholder: '',
          'aria-label': typeof label === 'string' ? label : 'Date',
        },
      }}
      sx={[
        {
          '& input[type="date"]': {
            color: hasValue ? 'inherit' : 'transparent',
          },
          '& input[type="date"]:focus': {
            color: 'inherit',
          },
          '& input[type="date"]::-webkit-datetime-edit': {
            visibility: hasValue ? 'visible' : 'hidden',
          },
          '& input[type="date"]:focus::-webkit-datetime-edit': {
            visibility: 'visible',
          },
          '& input[type="date"]::-webkit-datetime-edit-fields-wrapper': {
            visibility: hasValue ? 'visible' : 'hidden',
          },
          '& input[type="date"]:focus::-webkit-datetime-edit-fields-wrapper': {
            visibility: 'visible',
          },
          '& input[type="date"]::-webkit-calendar-picker-indicator': {
            cursor: 'pointer',
            opacity: hasValue ? 1 : 0.6,
          },
        },
        ...(Array.isArray(sx) ? sx : sx ? [sx] : []),
      ]}
      {...rest}
    />
  );
}
