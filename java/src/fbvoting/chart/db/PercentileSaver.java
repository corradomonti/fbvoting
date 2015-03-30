package fbvoting.chart.db;

import it.unimi.dsi.fastutil.longs.AbstractLongComparator;
import it.unimi.dsi.fastutil.longs.Long2DoubleMap;
import it.unimi.dsi.fastutil.longs.Long2IntMap;
import it.unimi.dsi.fastutil.longs.Long2IntOpenHashMap;
import it.unimi.dsi.fastutil.longs.LongArrays;
import it.unimi.dsi.logging.ProgressLogger;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.mongodb.BasicDBObject;
import com.mongodb.DBCollection;
import com.mongodb.DBObject;

public class PercentileSaver {
	
	private final static DBCollection COLLECTION = Db.getInstance().MONGODB.getCollection("userrank");
	
	private final static Logger LOGGER = LoggerFactory.getLogger(PercentileSaver.class);
	
	private final Long2DoubleMap userRanks;
	private final Category category;

	public PercentileSaver( Long2DoubleMap userRanks , Category category) {
		this.userRanks = userRanks;
		this.category = category;
	}
	
	public void computeAndSave() {
		Long2IntMap percentiles = computePercentiles();
		save(percentiles, userRanks);
	}

	public Long2IntMap computePercentiles() {
		LOGGER.info("Sorting user ranks for " + category + "...");
		
		long[] ids = userRanks.keySet().toLongArray();
		LongArrays.quickSort( ids, new AbstractLongComparator() {
			@Override
			public int compare( long k1, long k2 ) {
				return Double.compare( userRanks.get( k2 ), userRanks.get( k1 ) );
			}
		} );

		LOGGER.info("Computing user percentiles for " + category + "...");

		Long2IntMap id2NAbove = new Long2IntOpenHashMap();
		if (ids.length == 0)
			return id2NAbove;
		
		double lastRank = ids[ 0 ];
		int firstExAequoToUpdate = 0;
		
		ProgressLogger progressLogger = new ProgressLogger(LOGGER, "users");
		progressLogger.start();
		
		for ( int i = 1; i < ids.length; i++ ) {
			if ( userRanks.get( ids[ i ] ) != lastRank ) {

				while ( firstExAequoToUpdate < i ) {
					id2NAbove.put( ids[ firstExAequoToUpdate++ ], i );
				}

				lastRank = userRanks.get( ids[ i ] );

			}
			
			progressLogger.lightUpdate();
		}
		
		progressLogger.done();
		
		while ( firstExAequoToUpdate < ids.length ) {
			id2NAbove.put( ids[ firstExAequoToUpdate++ ], ids.length );
		}
		
		return id2NAbove;

	}
	
	public void save(Long2IntMap id2NAbove, Long2DoubleMap id2Rank) {
		LOGGER.info("Saving user ranks and percentiles on MongoDB for " + category + "...");
		ProgressLogger progressLogger = new ProgressLogger(LOGGER, "users");
		
		double totalPercent = (double) id2NAbove.size() / 100.0;
		
		progressLogger.start();
		
		for (long id : id2Rank.keySet()) {
			double percentile = (double) id2NAbove.get( id ) / totalPercent;
			if (percentile > 1 /* % */ )
				percentile = Math.round( percentile );
			
			DBObject selection = new BasicDBObject("_id", id);
			DBObject newFields = new BasicDBObject(
					"$set", 
					new BasicDBObject(category.getName(),
							new BasicDBObject	("score", id2Rank.get( id ))
								.append			( "perc", percentile )
					)
				);
			
			COLLECTION.update( selection, newFields, true /* upsert */ , false /* multi */);
			progressLogger.lightUpdate();
			
		}
		
		progressLogger.done();
	}

}
