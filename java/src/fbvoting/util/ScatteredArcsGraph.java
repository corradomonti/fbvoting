package fbvoting.util;

import static it.unimi.dsi.fastutil.HashCommon.bigArraySize;
import static it.unimi.dsi.fastutil.HashCommon.maxFill;
import it.unimi.dsi.fastutil.BigArrays;
import it.unimi.dsi.fastutil.Hash;
import it.unimi.dsi.fastutil.booleans.BooleanBigArrays;
import it.unimi.dsi.fastutil.ints.IntBigArrays;
import it.unimi.dsi.fastutil.io.BinIO;
import it.unimi.dsi.fastutil.longs.LongBigArrays;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import it.unimi.dsi.logging.ProgressLogger;
import it.unimi.dsi.webgraph.ImmutableSequentialGraph;
import it.unimi.dsi.webgraph.NodeIterator;
import it.unimi.dsi.webgraph.ScatteredArcsASCIIGraph;
import it.unimi.dsi.webgraph.Transform;

import java.io.File;
import java.io.IOException;
import java.util.Iterator;

public class ScatteredArcsGraph extends ImmutableSequentialGraph {

	private static final class Long2IntOpenHashBigMap implements java.io.Serializable, Cloneable, Hash {
		public static final long serialVersionUID = 0L;

		/** The big array of keys. */
		public transient long[][] key;

		/** The big array of values. */
		public transient int[][] value;

		/** The big array telling whether a position is used. */
		protected transient boolean[][] used;

		/** The acceptable load factor. */
		protected final float f;

		/** The current table size (always a power of 2). */
		protected transient long n;

		/** Threshold after which we rehash. It must be the table size times {@link #f}. */
		protected transient long maxFill;

		/** The mask for wrapping a position counter. */
		protected transient long mask;

		/** The mask for wrapping a segment counter. */
		protected transient int segmentMask;

		/** The mask for wrapping a base counter. */
		protected transient int baseMask;

		/** Number of entries in the set. */
		protected long size;

		/** Initialises the mask values. */
		private void initMasks() {
			mask = n - 1;
			/*
			 * Note that either we have more than one segment, and in this case all segments are
			 * BigArrays.SEGMENT_SIZE long, or we have exactly one segment whose length is a power of
			 * two.
			 */
			segmentMask = key[ 0 ].length - 1;
			baseMask = key.length - 1;
		}

		/**
		 * Creates a new hash big set.
		 * 
		 * <p>The actual table size will be the least power of two greater than
		 * <code>expected</code>/<code>f</code>.
		 * 
		 * @param expected the expected number of elements in the set.
		 * @param f the load factor.
		 */
		public Long2IntOpenHashBigMap( final long expected, final float f ) {
			if ( f <= 0 || f > 1 ) throw new IllegalArgumentException( "Load factor must be greater than 0 and smaller than or equal to 1" );
			if ( n < 0 ) throw new IllegalArgumentException( "The expected number of elements must be nonnegative" );
			this.f = f;
			n = bigArraySize( expected, f );
			maxFill = maxFill( n, f );
			key = LongBigArrays.newBigArray( n );
			value = IntBigArrays.newBigArray( n );
			used = BooleanBigArrays.newBigArray( n );
			initMasks();
		}

		/**
		 * Creates a new hash big set with initial expected {@link Hash#DEFAULT_INITIAL_SIZE} elements
		 * and {@link Hash#DEFAULT_LOAD_FACTOR} as load factor.
		 */

		public Long2IntOpenHashBigMap() {
			this( DEFAULT_INITIAL_SIZE, DEFAULT_LOAD_FACTOR );
		}

		public int put( final long k, final int v ) {
			final long h = it.unimi.dsi.fastutil.HashCommon.murmurHash3( k );

			// The starting point.
			int displ = (int)( h & segmentMask );
			int base = (int)( ( h & mask ) >>> BigArrays.SEGMENT_SHIFT );

			// There's always an unused entry.
			while ( used[ base ][ displ ] ) {
				if ( k == key[ base ][ displ ] ) {
					final int oldValue = value[ base ][ displ ];
					value[ base ][ displ ] = v;
					return oldValue;
				}
				base = ( base + ( ( displ = ( displ + 1 ) & segmentMask ) == 0 ? 1 : 0 ) ) & baseMask;
			}

			used[ base ][ displ ] = true;
			key[ base ][ displ ] = k;
			value[ base ][ displ ] = v;

			if ( ++size >= maxFill ) rehash( 2 * n );
			return -1;
		}

		public int get( final long k ) {
			final long h = it.unimi.dsi.fastutil.HashCommon.murmurHash3( k );

			// The starting point.
			int displ = (int)( h & segmentMask );
			int base = (int)( ( h & mask ) >>> BigArrays.SEGMENT_SHIFT );

			// There's always an unused entry.
			while ( used[ base ][ displ ] ) {
				if ( k == key[ base ][ displ ] ) return value[ base ][ displ ];
				base = ( base + ( ( displ = ( displ + 1 ) & segmentMask ) == 0 ? 1 : 0 ) ) & baseMask;
			}

			return -1;
		}

		protected void rehash( final long newN ) {
			final boolean used[][] = this.used;
			final long key[][] = this.key;
			final int[][] value = this.value;
			final boolean newUsed[][] = BooleanBigArrays.newBigArray( newN );
			final long newKey[][] = LongBigArrays.newBigArray( newN );
			final int newValue[][] = IntBigArrays.newBigArray( newN );
			final long newMask = newN - 1;
			final int newSegmentMask = newKey[ 0 ].length - 1;
			final int newBaseMask = newKey.length - 1;

			int base = 0, displ = 0;
			long h;
			long k;

			for ( long i = size; i-- != 0; ) {

				while ( !used[ base ][ displ ] )
					base = ( base + ( ( displ = ( displ + 1 ) & segmentMask ) == 0 ? 1 : 0 ) );

				k = key[ base ][ displ ];
				h = it.unimi.dsi.fastutil.HashCommon.murmurHash3( k );

				// The starting point.
				int d = (int)( h & newSegmentMask );
				int b = (int)( ( h & newMask ) >>> BigArrays.SEGMENT_SHIFT );

				while ( newUsed[ b ][ d ] )
					b = ( b + ( ( d = ( d + 1 ) & newSegmentMask ) == 0 ? 1 : 0 ) ) & newBaseMask;

				newUsed[ b ][ d ] = true;
				newKey[ b ][ d ] = k;
				newValue[ b ][ d ] = value[ base ][ displ ];

				base = ( base + ( ( displ = ( displ + 1 ) & segmentMask ) == 0 ? 1 : 0 ) );
			}

			this.n = newN;
			this.key = newKey;
			this.value = newValue;
			this.used = newUsed;
			initMasks();
			maxFill = maxFill( n, f );
		}

		public void compact() {
			int base = 0, displ = 0, b = 0, d = 0;
			for( long i = size; i-- != 0; ) {
				while ( ! used[ base ][ displ ] ) base = ( base + ( ( displ = ( displ + 1 ) & segmentMask ) == 0 ? 1 : 0 ) ) & baseMask;
				key[ b ][ d ] = key[ base ][ displ ];
				value[ b ][ d ] = value[ base ][ displ ];
				base = ( base + ( ( displ = ( displ + 1 ) & segmentMask ) == 0 ? 1 : 0 ) ) & baseMask;
				b = ( b + ( ( d = ( d + 1 ) & segmentMask ) == 0 ? 1 : 0 ) ) & baseMask;
			}
		}
		
		public long size() {
			return size;
		}
	}

	/** The default batch size. */
	public static final int DEFAULT_BATCH_SIZE = 1000000;
	/** The batch graph used to return node iterators. */
	private Transform.BatchGraph batchGraph;
	/** The list of identifiers in order of appearance. */
	public long[] ids;

	public int numNodes() {
		if ( batchGraph == null ) throw new UnsupportedOperationException( "The number of nodes is unknown (you need to exhaust the input)" );
		return batchGraph.numNodes();
	}
	
	public long numArcs() {
		if ( batchGraph == null ) throw new UnsupportedOperationException( "The number of arcs is unknown (you need to exhaust the input)" );
		return batchGraph.numArcs();
	}
	
	@Override
	public NodeIterator nodeIterator( final int from ) {
		return batchGraph.nodeIterator( from );
	}

	public ScatteredArcsGraph( final Iterator<long[]> arcs, final boolean symmetrize, final boolean noLoops, final int batchSize, final File tempDir, final ProgressLogger pl ) throws IOException {
		Long2IntOpenHashBigMap map = new Long2IntOpenHashBigMap();

		int numNodes = -1;

		int j;
		int[] source = new int[ batchSize ] , target = new int[ batchSize ];
		ObjectArrayList<File> batches = new ObjectArrayList<File>();

		if ( pl != null ) {
			pl.itemsName = "arcs";
			pl.start( "Creating sorted batches..." );
		}

		j = 0;
		long pairs = 0; // Number of pairs
		while( arcs.hasNext() ) {
			long[] arc = arcs.next();
			final long sl = arc[ 0 ];
			int s = map.get( sl );
			if ( s == -1 ) map.put( sl, s = (int)map.size() );
			final long tl = arc[ 1 ];
			int t = map.get( tl );
			if ( t == -1 ) map.put( tl, t = (int)map.size() );

			if ( s != t || ! noLoops ) { 
				source[ j ] = s;
				target[ j++ ] = t;

				if ( j == batchSize ) {
					pairs += Transform.processBatch( batchSize, source, target, tempDir, batches );
					j = 0;
				}

				if ( symmetrize && s != t ) {
					source[ j ] = t;
					target[ j++ ] = s;
					if ( j == batchSize ) {
						pairs += Transform.processBatch( batchSize, source, target, tempDir, batches );
						j = 0;
					}
				}
				
				if ( pl != null ) pl.lightUpdate();
			}
		}

		if ( j != 0 ) pairs += Transform.processBatch( j, source, target, tempDir, batches );

		if ( pl != null ) pl.done();
		
		numNodes = (int)map.size();
		source = null;
		target = null;

		map.compact();
		
		final File keyFile = File.createTempFile( ScatteredArcsASCIIGraph.class.getSimpleName(), "keys", tempDir );
		keyFile.deleteOnExit();
		final File valueFile = File.createTempFile( ScatteredArcsASCIIGraph.class.getSimpleName(), "values", tempDir );
		valueFile.deleteOnExit();

		BinIO.storeLongs( map.key, 0, map.size(), keyFile );
		BinIO.storeInts( map.value, 0, map.size(), valueFile );
		
		map = null;
		
		long[][] key = BinIO.loadLongsBig( keyFile );
		keyFile.delete();
		int[][] value = BinIO.loadIntsBig( valueFile );
		valueFile.delete();

		ids = new long[ numNodes ];

		final long[] result = new long[ numNodes ];
		for( int i = numNodes; i--!= 0; ) result[ IntBigArrays.get( value, i ) ] = LongBigArrays.get( key, i );
		ids = result;
		
		key = null;
		value = null;

		batchGraph = new Transform.BatchGraph( numNodes, pairs, batches );
	}
}
