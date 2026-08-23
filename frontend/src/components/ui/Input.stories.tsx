import type { Meta, StoryObj } from '@storybook/react';
import { Input } from './Input';
import { Label } from './Label';

const meta: Meta<typeof Input> = {
  title: 'UI/Input',
  component: Input,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A flexible input component with label support and validation states.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    type: {
      control: 'select',
      options: ['text', 'email', 'password', 'number', 'tel', 'url', 'search'],
      description: 'The type of input',
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the input is disabled',
    },
    required: {
      control: 'boolean',
      description: 'Whether the input is required',
    },
    placeholder: { control: 'text' },
    value: { control: 'text' },
    error: { control: 'boolean' },
  },
  decorators: [
    (Story) => (
      <div className="w-[300px]">
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof Input>;

export const Default: Story = {
  args: {
    placeholder: 'Enter text...',
  },
};

export const WithLabel: Story = {
  render: () => (
    <div className="space-y-2">
      <Label htmlFor="email">Email Address</Label>
      <Input id="email" type="email" placeholder="you@example.com" />
    </div>
  ),
};

export const WithValue: Story = {
  args: {
    value: 'Pre-filled value',
    placeholder: 'Enter text...',
  },
};

export const Disabled: Story = {
  args: {
    disabled: true,
    placeholder: 'Disabled input',
  },
};

export const Required: Story = {
  render: () => (
    <div className="space-y-2">
      <Label htmlFor="required-field">Required Field *</Label>
      <Input id="required-field" required placeholder="This field is required" />
    </div>
  ),
};

export const Email: Story = {
  render: () => (
    <div className="space-y-2">
      <Label htmlFor="email-input">Email</Label>
      <Input id="email-input" type="email" placeholder="you@example.com" />
    </div>
  ),
};

export const Password: Story = {
  render: () => (
    <div className="space-y-2">
      <Label htmlFor="password-input">Password</Label>
      <Input id="password-input" type="password" placeholder="Enter password" />
    </div>
  ),
};

export const WithError: Story = {
  render: () => (
    <div className="space-y-2">
      <Label htmlFor="error-input" className="text-destructive">Email (with error)</Label>
      <Input id="error-input" type="email" value="invalid-email" className="border-destructive focus:border-destructive focus:ring-destructive" />
      <p className="text-sm text-destructive">Please enter a valid email address</p>
    </div>
  ),
};

export const Search: Story = {
  args: {
    type: 'search',
    placeholder: 'Search...',
  },
};

export const AllTypes: Story = {
  render: () => (
    <div className="space-y-4 w-[300px]">
      {['text', 'email', 'password', 'number', 'tel', 'url', 'search'].map((type) => (
        <div key={type} className="space-y-1">
          <Label htmlFor={`input-${type}`}>{type}</Label>
          <Input id={`input-${type}`} type={type as any} placeholder={`Enter ${type}...`} />
        </div>
      ))}
    </div>
  ),
};