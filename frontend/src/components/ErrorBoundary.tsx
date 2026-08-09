import { Component, type ErrorInfo, type ReactNode } from 'react';
import { Box, Button, Typography, Alert } from '@mui/material';
import { Refresh } from '@mui/icons-material';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  message: string;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: '' };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message || 'Unexpected error' };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, message: '' });
  };

  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{ p: 4, maxWidth: 560, mx: 'auto', mt: 8 }}>
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              {this.props.fallbackTitle || 'Something went wrong'}
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              {this.state.message}
            </Typography>
          </Alert>
          <Button variant="contained" startIcon={<Refresh />} onClick={this.handleReset}>
            Try Again
          </Button>
          <Button sx={{ ml: 1 }} onClick={() => window.location.assign('/')}>
            Go to Dashboard
          </Button>
        </Box>
      );
    }
    return this.props.children;
  }
}
