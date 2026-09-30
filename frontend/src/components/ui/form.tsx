'use client';

import * as React from 'react';
import * as Slot from '@radix-ui/react-slot';
import { Controller, ControllerProps, FieldPath, FieldValues, UseFormProps, UseFormReturn, useForm as useReactHookForm } from 'react-hook-form';
import { cn } from '../../utils/cn';
import { Label } from './label';
import { Input } from './input';
import { Textarea } from './textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './select';

const Form = React.forwardRef<HTMLFormElement, React.FormHTMLAttributes<HTMLFormElement>>(
  ({ className, ...props }, ref) => (
    <form ref={ref} className={cn('space-y-8', className)} {...props} />
  )
);
Form.displayName = 'Form';

type FormFieldContextValue<TFieldValues extends FieldValues> = {
  name: FieldPath<TFieldValues>;
};

const FormFieldContext = React.createContext<FormFieldContextValue<any>>({} as FormFieldContextValue<any>);

const FormField = <TFieldValues extends FieldValues = FieldValues>({
  ...props
}: ControllerProps<TFieldValues>) => {
  return (
    <FormFieldContext.Provider value={{ name: props.name }}>
      <Controller {...props} />
    </FormFieldContext.Provider>
  );
};

const useFormField = () => {
  const fieldContext = React.useContext(FormFieldContext);
  const itemContext = React.useContext(FormItemContext);
  const { getFieldState, formState } = React.useContext(FormProviderContext);

  const fieldState = getFieldState(fieldContext.name, formState);

  if (!fieldContext) {
    throw new Error('useFormField should be used within <FormField>');
  }

  const { id } = itemContext;

  return {
    id,
    name: fieldContext.name,
    formItemId: `${id}-form-item`,
    formDescriptionId: `${id}-form-item-description`,
    formMessageId: `${id}-form-item-message`,
    ...fieldState,
  };
};

const FormProviderContext = React.createContext<{
  getFieldState: (name: string, formState: any) => any;
  formState: any;
}>({} as any);

export interface FormProviderProps<TFieldValues extends FieldValues = FieldValues>
  extends UseFormProps<TFieldValues> {
  children: React.ReactNode;
}

function FormProvider<TFieldValues extends FieldValues = FieldValues>({
  children,
  ...props
}: FormProviderProps<TFieldValues>) {
  const methods = useReactHookForm<TFieldValues>(props);

  return (
    <FormProviderContext.Provider value={{ getFieldState: methods.getFieldState, formState: methods.formState }}>
      <Form {...methods}><FormProviderContext.Provider value={{ getFieldState: methods.getFieldState, formState: methods.formState }}>{children}</FormProviderContext.Provider></Form>
    </FormProviderContext.Provider>
  );
}

const FormItemContext = React.createContext<{ id: string }>({} as any);

const FormItem = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & { id?: string }>(
  ({ className, id: idProp, ...props }, ref) => {
    const id = idProp || React.useId();
    return (
      <FormItemContext.Provider value={{ id }}>
        <div ref={ref} className={cn('space-y-2', className)} {...props} />
      </FormItemContext.Provider>
    );
  }
);
FormItem.displayName = 'FormItem';

const FormLabel = React.forwardRef<HTMLLabelElement, React.LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => {
    const { error, formItemId } = useFormField();
    return (
      <Label
        ref={ref}
        className={cn(error && 'text-destructive', className)}
        htmlFor={formItemId}
        {...props}
      />
    );
  }
);
FormLabel.displayName = 'FormLabel';

const FormControl = React.forwardRef<any, React.ComponentPropsWithoutRef<typeof Slot>>(
  ({ className, ...props }, ref) => {
    const { error, formItemId, formDescriptionId, formMessageId } = useFormField();
    return (
      <Slot
        ref={ref}
        id={formItemId}
        aria-describedby={
          !error ? `${formDescriptionId}` : `${formDescriptionId} ${formMessageId}`
        }
        aria-invalid={!!error}
        className={cn('', className)}
        {...props}
      />
    );
  }
);
FormControl.displayName = 'FormControl';

const FormDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => {
    const { formDescriptionId } = useFormField();
    return (
      <p
        ref={ref}
        id={formDescriptionId}
        className={cn('text-sm text-muted-foreground', className)}
        {...props}
      />
    );
  }
);
FormDescription.displayName = 'FormDescription';

const FormMessage = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, children, ...props }, ref) => {
    const { error, formMessageId } = useFormField();
    const body = error ? String(error?.message) : children;
    return (
      <p
        ref={ref}
        id={formMessageId}
        className={cn('text-sm font-medium text-destructive', className)}
        {...props}
      >
        {body}
      </p>
    );
  }
);
FormMessage.displayName = 'FormMessage';

export {
  useFormField,
  Form,
  FormProvider,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
  Input,
  Textarea,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Label,
};