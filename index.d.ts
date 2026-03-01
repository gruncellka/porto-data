/**
 * Type declarations for @gruncellka/porto-data (npm).
 * Default export is metadata; data files live under porto_data/.
 */

export interface FileRef {
    path: string;
    checksum: string;
    size: number;
    url?: string;
}

export interface EntityMeta {
    data: FileRef;
    schema: FileRef;
}

export interface PortoDataMetadata {
    project: {
        name: string;
        version: string;
        description: string;
    };
    generated_at: string;
    entities: Record<string, EntityMeta>;
    checksums: {
        algorithm: string;
        note: string;
    };
}

declare const metadata: PortoDataMetadata;
export default metadata;
