/**
 * Type declarations for @gruncellka/porto-data (npm).
 * Default export matches porto_data/metadata.json (generated).
 */

export interface FileRef {
    path: string
    checksum: string
    size: number
}

export interface SchemaRef extends FileRef {
    url: string
}

/** One logical entity: paired data file + schema file. */
export interface EntityMeta {
    data: FileRef
    schema: SchemaRef
}

export interface PortoDataMetadata {
    $schema: string
    project: {
        name: string
        version: string
        description: string
    }
    generated_at: string
    /** Shared policy files (e.g. jurisdictions, restrictions). */
    policy: Record<string, EntityMeta>
    /** Shared format files (e.g. envelopes, layouts). */
    formats: Record<string, EntityMeta>
    /** Bundle registry entries (e.g. providers.json). */
    registry: Record<string, EntityMeta>
    /** Per postal provider: entity name → data + schema refs. */
    providers: Record<string, Record<string, EntityMeta>>
    /** Root manifest files: mappings.json and providers.json. */
    bundle?: {
        mappings: EntityMeta
        providers_registry: EntityMeta
    }
    checksums: {
        algorithm: 'SHA-256'
        note: string
    }
}

declare const metadata: PortoDataMetadata
export default metadata
