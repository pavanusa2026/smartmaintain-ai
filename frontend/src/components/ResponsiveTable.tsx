import { Box, Card, CardContent, useMediaQuery, useTheme } from '@mui/material';
import type { ReactNode } from 'react';

interface Column<T> {
  key: string;
  label: string;
  render: (row: T) => ReactNode;
  hideOnMobile?: boolean;
}

interface ResponsiveTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  keyField: keyof T & string;
  onRowClick?: (row: T) => void;
}

export default function ResponsiveTable<T extends Record<string, unknown>>({
  columns,
  rows,
  keyField,
  onRowClick,
}: ResponsiveTableProps<T>) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const visibleCols = isMobile ? columns.filter((c) => !c.hideOnMobile) : columns;

  if (isMobile) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        {rows.map((row) => (
          <Card
            key={String(row[keyField])}
            variant="outlined"
            sx={{ cursor: onRowClick ? 'pointer' : 'default' }}
            onClick={() => onRowClick?.(row)}
          >
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              {visibleCols.map((col) => (
                <Box key={col.key} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5, gap: 1 }}>
                  <Box component="span" sx={{ fontSize: 12, color: 'text.secondary', flexShrink: 0 }}>
                    {col.label}
                  </Box>
                  <Box sx={{ textAlign: 'right', fontSize: 14 }}>{col.render(row)}</Box>
                </Box>
              ))}
            </CardContent>
          </Card>
        ))}
      </Box>
    );
  }

  return (
    <Box sx={{ overflowX: 'auto', width: '100%' }}>
      <Box component="table" sx={{ width: '100%', borderCollapse: 'collapse', minWidth: 600 }}>
        <Box component="thead">
          <Box component="tr" sx={{ borderBottom: '2px solid', borderColor: 'divider' }}>
            {visibleCols.map((col) => (
              <Box
                component="th"
                key={col.key}
                sx={{ textAlign: 'left', py: 1.5, px: 2, fontSize: 13, fontWeight: 600, color: 'text.secondary' }}
              >
                {col.label}
              </Box>
            ))}
          </Box>
        </Box>
        <Box component="tbody">
          {rows.map((row) => (
            <Box
              component="tr"
              key={String(row[keyField])}
              onClick={() => onRowClick?.(row)}
              sx={{
                borderBottom: '1px solid',
                borderColor: 'divider',
                cursor: onRowClick ? 'pointer' : 'default',
                '&:hover': onRowClick ? { bgcolor: 'action.hover' } : {},
              }}
            >
              {visibleCols.map((col) => (
                <Box component="td" key={col.key} sx={{ py: 1.5, px: 2, fontSize: 14 }}>
                  {col.render(row)}
                </Box>
              ))}
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  );
}
