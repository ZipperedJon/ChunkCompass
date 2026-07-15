/* Chunk Compass native interface over cubiomes.
 *
 * Exposes a small, batch-friendly C API for the Python app:
 *   - sm_fill_biomes      : fill a grid of biome ids in one call (fast render)
 *   - sm_find_structures  : find structures of one type within a block area
 *   - sm_get_spawn        : approximate world spawn
 *   - sm_mc_newest        : newest MC version constant the engine supports
 *
 * Built into cubiomes.dll with ziglang; see build_native.py.
 */
#include "generator.h"
#include "finders.h"
#include "biomenoise.h"
#include <stdint.h>
#include <stdlib.h>

#if defined(_WIN32)
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

/* Floored integer division (handles negatives like Python's //). */
static int ifloordiv(int a, int b)
{
    int q = a / b;
    if ((a % b != 0) && ((a < 0) != (b < 0)))
        q--;
    return q;
}

EXPORT int sm_mc_newest(void)
{
    return MC_NEWEST;
}

/* Cached single-point biome lookup, for cheap mouse-hover queries. The
 * generator is only re-initialised when the version/seed/dimension change. */
static Generator g_hover;
static int g_hover_ready = 0;
static int g_hover_mc = -1;
static uint64_t g_hover_seed = 0;
static int g_hover_dim = 999;

EXPORT int sm_biome_at(int mc, uint64_t seed, int dim, int x, int y, int z)
{
    if (!g_hover_ready || mc != g_hover_mc || seed != g_hover_seed || dim != g_hover_dim)
    {
        setupGenerator(&g_hover, mc, 0);
        applySeed(&g_hover, dim, seed);
        g_hover_mc = mc;
        g_hover_seed = seed;
        g_hover_dim = dim;
        g_hover_ready = 1;
    }
    return getBiomeAt(&g_hover, 1, x, y, z);
}

/* Fill out[cols*rows] with biome ids. Sample point for cell (i, j) is
 * x = x0 + (i + 0.5) * stepx,  z = z0 + (j + 0.5) * stepz. */
EXPORT int sm_fill_biomes(int mc, uint64_t seed, int dim, int y,
        int x0, int z0, double stepx, double stepz,
        int cols, int rows, int *out)
{
    Generator g;
    setupGenerator(&g, mc, 0);
    applySeed(&g, dim, seed);

    for (int j = 0; j < rows; j++)
    {
        int z = (int)(z0 + (j + 0.5) * stepz);
        for (int i = 0; i < cols; i++)
        {
            int x = (int)(x0 + (i + 0.5) * stepx);
            out[j * cols + i] = getBiomeAt(&g, 1, x, y, z);
        }
    }
    return 0;
}

/* Find structures of type `stype` whose generation attempt lands inside the
 * block rectangle [x0,x1] x [z0,z1]. Writes up to `maxout` (x,z) int pairs to
 * `out`. Returns the number found, or -1 if the area spans too many regions
 * (caller should zoom in). */
EXPORT int sm_find_structures(int stype, int mc, uint64_t seed, int dim,
        int x0, int z0, int x1, int z1, int *out, int maxout)
{
    StructureConfig sc;
    if (!getStructureConfig(stype, mc, &sc))
        return 0;
    int region_blocks = (int)sc.regionSize * 16;
    if (region_blocks <= 0)
        return 0;

    int r0x = ifloordiv(x0, region_blocks);
    int r1x = ifloordiv(x1, region_blocks);
    int r0z = ifloordiv(z0, region_blocks);
    int r1z = ifloordiv(z1, region_blocks);

    long long nreg = (long long)(r1x - r0x + 1) * (long long)(r1z - r0z + 1);
    if (nreg > 20000)
        return -1;

    Generator g;
    setupGenerator(&g, mc, 0);
    applySeed(&g, dim, seed);

    int count = 0;
    for (int rx = r0x; rx <= r1x; rx++)
    {
        for (int rz = r0z; rz <= r1z; rz++)
        {
            Pos p;
            if (!getStructurePos(stype, mc, seed, rx, rz, &p))
                continue;
            if (p.x < x0 || p.x > x1 || p.z < z0 || p.z > z1)
                continue;
            if (!isViableStructurePos(stype, &g, p.x, p.z, 0))
                continue;
            if (count < maxout)
            {
                out[2 * count] = p.x;
                out[2 * count + 1] = p.z;
            }
            count++;
        }
    }
    return count;
}

/* Fill out[cols*rows] with approximate Overworld surface heights (in blocks).
 * Sample point for cell (i, j) is x = x0 + (i+0.5)*stepx, likewise z.
 * Only meaningful for 1.18+ (noise generation). */
EXPORT int sm_fill_heights(int mc, uint64_t seed, int dim, int x0, int z0,
        double stepx, double stepz, int cols, int rows, float *out)
{
    Generator g;
    setupGenerator(&g, mc, 0);
    applySeed(&g, dim, seed);
    SurfaceNoise sn;
    initSurfaceNoise(&sn, dim, seed);

    for (int j = 0; j < rows; j++)
    {
        int bz = (int)(z0 + (j + 0.5) * stepz);
        for (int i = 0; i < cols; i++)
        {
            int bx = (int)(x0 + (i + 0.5) * stepx);
            float y = 0.0f;
            /* mapApproxHeight uses 1:4 horizontal scale. */
            mapApproxHeight(&y, 0, &g, &sn, bx >> 2, bz >> 2, 1, 1);
            out[j * cols + i] = y;
        }
    }
    return 0;
}

/* Find overworld strongholds (up to maxout, in generation order). Writes (x,z)
 * block pairs to out; returns the number written. */
EXPORT int sm_find_strongholds(int mc, uint64_t seed, int maxout, int *out)
{
    Generator g;
    setupGenerator(&g, mc, 0);
    applySeed(&g, DIM_OVERWORLD, seed);
    StrongholdIter sh;
    initFirstStronghold(&sh, mc, seed);
    int count = 0;
    while (count < maxout)
    {
        int more = nextStronghold(&sh, &g);
        out[2 * count] = sh.pos.x;
        out[2 * count + 1] = sh.pos.z;
        count++;
        if (more <= 0)
            break;
    }
    return count;
}

/* Find mineshaft chunks within a block area. Writes (x,z) pairs to out; returns
 * the number found (or -1 if the area spans too many chunks). */
EXPORT int sm_find_mineshafts(int mc, uint64_t seed,
        int x0, int z0, int x1, int z1, int *out, int maxout)
{
    int cx0 = x0 >> 4, cz0 = z0 >> 4, cx1 = x1 >> 4, cz1 = z1 >> 4;
    int cw = cx1 - cx0 + 1, ch = cz1 - cz0 + 1;
    if (cw < 1 || ch < 1)
        return 0;
    if ((long long)cw * ch > 200000)
        return -1;
    Pos *buf = (Pos *)malloc(sizeof(Pos) * (maxout > 0 ? maxout : 1));
    if (!buf)
        return 0;
    int n = getMineshafts(mc, seed, cx0, cz0, cw, ch, buf, maxout);
    int m = n < maxout ? n : maxout;
    for (int i = 0; i < m; i++)
    {
        out[2 * i] = buf[i].x;
        out[2 * i + 1] = buf[i].z;
    }
    free(buf);
    return n;
}

/* Nearest block (coarse grid) whose biome == target, searching outward from
 * (cx,cz) up to maxradius in steps of `step`. Writes (x,z) to out; returns 1 if
 * found, else 0. */
EXPORT int sm_nearest_biome(int mc, uint64_t seed, int dim, int y,
        int cx, int cz, int target, int maxradius, int step, int *out)
{
    Generator g;
    setupGenerator(&g, mc, 0);
    applySeed(&g, dim, seed);
    if (step < 1)
        step = 1;
    long long bestd = -1;
    int bx = 0, bz = 0, found = 0;
    for (int dx = -maxradius; dx <= maxradius; dx += step)
    {
        for (int dz = -maxradius; dz <= maxradius; dz += step)
        {
            int x = cx + dx, z = cz + dz;
            if (getBiomeAt(&g, 1, x, y, z) != target)
                continue;
            long long d = (long long)dx * dx + (long long)dz * dz;
            if (!found || d < bestd)
            {
                bestd = d;
                bx = x;
                bz = z;
                found = 1;
            }
        }
    }
    if (found)
    {
        out[0] = bx;
        out[1] = bz;
    }
    return found;
}

/* Approximate world spawn (fast). Writes {x, z} to out. */
EXPORT int sm_get_spawn(int mc, uint64_t seed, int *out)
{
    Generator g;
    setupGenerator(&g, mc, 0);
    applySeed(&g, DIM_OVERWORLD, seed);
    Pos p = estimateSpawn(&g, 0);
    out[0] = p.x;
    out[1] = p.z;
    return 0;
}
