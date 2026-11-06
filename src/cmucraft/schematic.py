"""Sponge v2 footprint schematic: a flat survey model, not actual buildings."""
import numpy as np
import nbtlib as nbt


def export(grid, path):
    size = grid.shape[0]
    # Array order Y,Z,X -> x + z*Width + y*Width*Length.
    blocks = np.zeros((2,size,size),dtype=np.int8)
    blocks[0,:,:] = 1  # generic flat grass platform, not surveyed terrain
    blocks[1,grid>0] = 2  # one-block-high footprint, not inferred building height
    palette = {'minecraft:air':nbt.Int(0),
               'minecraft:grass_block[snowy=false]':nbt.Int(1),
               'minecraft:stone_bricks':nbt.Int(2)}
    # All palette IDs <128, so each varint is exactly one byte.
    file = nbt.File({
        'Version':nbt.Int(2),'DataVersion':nbt.Int(3465),
        'Width':nbt.Short(size),'Height':nbt.Short(2),'Length':nbt.Short(size),
        'Offset':nbt.IntArray([0,0,0]),'PaletteMax':nbt.Int(len(palette)),
        'Palette':nbt.Compound(palette),'BlockData':nbt.ByteArray(blocks.ravel()),
        'BlockEntities':nbt.List[nbt.Compound]([]),'Entities':nbt.List[nbt.Compound]([]),
        'Metadata':nbt.Compound({'Name':nbt.String('CMUcraft footprint survey prototype'),
            'Author':nbt.String('CMUcraft; footprint data © OpenStreetMap contributors'),
            'Description':nbt.String('1 block = 1 metre; flat placeholder ground; heights NOT real')})
    },root_name='Schematic',gzipped=True)
    file.save(str(path))
