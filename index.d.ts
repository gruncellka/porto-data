/**
 * Type declarations for @gruncellka/porto-data (npm).
 * Default export matches porto_data/metadata.json (generated).
 */

export interface FileRef {
    path: string
    checksum: string
    size: number
    url?: string
}

/** One logical entity: paired data file + schema file. */
export interface EntityMeta {
    data: FileRef
    schema: FileRef
}

export interface PortoDataMetadata {
    project: {
        name: string
        version: string
        description: string
    }
    generated_at: string
    /** Shared files (e.g. envelopes, restrictions, providers, jurisdictions). */
    global: Record<string, EntityMeta>
    /** Per postal provider: entity name → data + schema refs. */
    providers: Record<string, Record<string, EntityMeta>>
    checksums: {
        algorithm: string
        note: string
    }
}

declare const metadata: PortoDataMetadata
export default metadata
