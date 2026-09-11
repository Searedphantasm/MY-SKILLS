---
name: form-creation
description: Design, review, or implement clear, accessible, low-friction forms in web or mobile products. Use when Codex is working on form UX, multi-step forms, checkout or onboarding flows, admin create/edit forms, validation behavior, accessibility requirements, mobile form layout, or form implementation structure.
---

# Form Creation

## Purpose

Use this skill whenever you design, review, or implement forms in a web or mobile product. The goal is to create forms that are clear, accessible, low-friction, and easy to complete without overwhelming the user.

## Core Rule

For long forms, split the experience into tabs, steps, or a wizard with a visible progress indicator. Never stack multiple large forms vertically on one page.

A long form is any form that has many fields, asks for multiple kinds of information, requires user effort beyond a quick task, or contains more than one logical section such as profile, address, shipping, payment, settings, permissions, or review.

## Form Structure

Start by identifying the user's goal, not the database model. The form should follow the user's mental flow, not the backend table structure.

Group related fields together. Each group should answer one clear question: who is this about, where should it go, how should it be paid, what settings should apply, or what should happen next.

Use a single-column layout by default. Multi-column forms can make scanning harder, especially on mobile, and can confuse the reading order for keyboard and screen-reader users.

Keep the primary action obvious. Use one main submit button per step or form. Secondary actions such as cancel, save draft, or back should be visually less prominent.

Avoid optional fields unless they clearly help the user or the business. If a field is not needed now, remove it, defer it, or move it into an advanced section.

## Long Forms

When a form is long, divide it into steps or tabs based on user intent. Good step boundaries usually match real-world stages, such as:

- Basic information
- Address or location
- Shipping or delivery
- Payment
- Review and confirm

Each step should have a clear title, a short explanation when needed, and only the fields required for that stage.

Always show progress for multi-step forms. The progress indicator should match the actual steps one-to-one and should not hide or merge important steps. Completed steps should be reviewable, and when safe, users should be able to go back without losing data.

Prefer steps or a wizard for linear tasks where order matters. Prefer tabs for non-linear settings forms where users may jump between independent sections. Do not use tabs for a process that must be completed in sequence unless the tab behavior clearly supports validation and progress.

For accordion-style long forms, collapse completed sections into readable summaries so users can review what they entered without reopening every section.

Persist progress whenever the form takes meaningful effort. For checkout, onboarding, profile completion, admin creation flows, and multi-step applications, protect users from accidental data loss through autosave, draft save, or clear navigation warnings.

## Field Design

Use clear labels above fields. Do not rely on placeholders as labels because placeholders disappear when the user types and are often lower contrast.

Use helper text only when it removes uncertainty. Good helper text explains format, consequences, or where to find the requested information. Bad helper text repeats the label.

Use the right input type and control:

- Text input for short free text
- Textarea for longer free text
- Select only when choices are known and not too many
- Radio buttons when users should compare a small set of choices
- Checkboxes for independent yes/no choices
- Date picker only when it is better than typing
- Searchable combobox for large option sets
- File upload with clear limits and accepted formats

Use sensible defaults when they are safe and likely correct. Never default users into consent, paid options, destructive actions, or privacy-sensitive choices.

Mark optional fields as optional when most fields are required. Mark required fields only when most fields are optional. Do not mark every field with visual noise.

## Validation

Validate as close to the field as possible, but do not interrupt typing too aggressively. Prefer validation on blur, step submit, or after the user has entered enough information.

Write error messages in plain language. State what is wrong and how to fix it. Match the error message wording to the field label so the user can connect the message to the field.

Show errors in text, not color alone. Place the error near the relevant field and include an error summary at the top when the form has multiple errors.

Preserve user input after validation fails. Never clear a form because one field is invalid.

For server-side errors, explain whether the user can fix the issue. For example, distinguish between "This email is already used" and "We could not save this right now. Try again."

## Accessibility Requirements

Every input must have a programmatically associated label.

The visible label should match or be included in the accessible name so voice control and assistive technologies work predictably.

Use semantic HTML controls before custom components. If a custom component is necessary, it must support keyboard navigation, focus states, ARIA semantics, and screen-reader announcements.

Maintain a logical focus order. When a user submits a form with errors, move focus to the error summary or the first invalid field.

Use adequate contrast for text, borders, focus rings, errors, disabled states, and helper text.

Do not disable submit buttons without explaining why. A disabled button can trap users because they may not know what is missing. Prefer allowing submit and showing clear validation, or show a visible checklist of missing requirements.

## Mobile UX

Design mobile-first for forms. Use large touch targets, enough spacing, and the correct virtual keyboard for each input type.

Avoid dense horizontal layouts. On mobile, each field should usually take the full width.

Keep sticky actions only when they do not cover content or error messages. For long mobile forms, a sticky next or save button can help, but it must not hide the current field.

Minimize typing. Use autocomplete, saved data, input masks where helpful, and device capabilities such as camera upload or address suggestions when appropriate.

## Data, Privacy, and Trust

Ask only for information that is necessary for the current user goal. If sensitive information is required, explain why it is needed and how it will be used.

Make destructive actions explicit and reversible when possible. Use confirmation only for actions with real consequences, not routine saves.

For payment, identity, legal, medical, or high-stakes forms, include a review step before final submission.

Do not surprise users after submission. Make the result clear: saved, submitted, pending review, payment complete, account created, or action failed.

## Implementation Guidance

Separate form state, validation schema, submission logic, and UI components. Do not let UI layout become the source of business rules.

Use schema validation for both client and server. Client validation improves feedback; server validation is the source of truth.

Use progressive enhancement where possible. A form should not lose core functionality just because JavaScript behavior fails, unless the product explicitly requires an app-only experience.

Prevent duplicate submissions with loading states and idempotent server handling. The UI should show that the action is processing and should not create duplicate records if the user clicks twice.

For multi-step forms, decide whether data is saved per step or only at final submit. If saving per step, make partial state explicit and recoverable. If final-only, protect against accidental navigation loss.

## Review Checklist

Before shipping a form, check the following:

- The form follows the user's task flow, not only the database structure.
- Long forms are split into steps, tabs, or sections with progress indication.
- Multiple large forms are not stacked vertically on one page.
- Each step has one clear purpose.
- Every field has a visible and programmatic label.
- Optional and required fields are communicated consistently.
- Validation messages explain what happened and how to fix it.
- Errors are shown near fields and summarized when there are multiple errors.
- User input is preserved after errors.
- Keyboard navigation and focus order work correctly.
- Mobile layout is single-column and touch-friendly.
- Submission states prevent duplicate actions.
- Sensitive fields have clear justification.
- Final high-stakes actions include review or confirmation.

## Default Recommendation

When unsure, choose the simpler form. Fewer fields, clearer labels, one-column layout, visible progress, and strong error handling usually outperform visually complex forms.
