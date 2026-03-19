# app/schemas — Pydantic v2 Schemas

## Purpose
Request validation and response serialization for all API endpoints.
One schema file per model, never share schema files across models.

## Pattern
Each file exports: {Model}Base, {Model}Create, {Model}Update, {Model}Read
- Base: shared fields
- Create: fields accepted on POST
- Update: fields accepted on PATCH (all Optional)
- Read: fields returned in responses (includes id, created_at, etc.)

## Rules
- Never include `encrypted_key` in any APIKey schema
- APIKey responses show only last 4 chars of key as `masked_key: str`
- Never return raw JSONB blobs directly — type them properly in schemas
- Import enums from `app.models.enums`, not redefined here
