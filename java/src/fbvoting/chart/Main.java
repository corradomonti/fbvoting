package fbvoting.chart;

import it.unimi.dsi.fastutil.longs.Long2DoubleMap;
import it.unimi.dsi.logging.ProgressLogger;

import java.io.IOException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import cern.colt.Arrays;

import com.martiansoftware.jsap.FlaggedOption;
import com.martiansoftware.jsap.JSAP;
import com.martiansoftware.jsap.JSAPException;
import com.martiansoftware.jsap.JSAPResult;
import com.martiansoftware.jsap.Parameter;
import com.martiansoftware.jsap.SimpleJSAP;
import com.martiansoftware.jsap.UnflaggedOption;

import fbvoting.chart.db.Category;
import fbvoting.chart.db.ItemRanker;
import fbvoting.chart.db.PercentileSaver;

public class Main {

	private final static Logger LOGGER = LoggerFactory.getLogger(Main.class);
	
	public static void main(String[] rawArguments) throws IOException, JSAPException {
		SimpleJSAP jsap = new SimpleJSAP(
				"fbvoting.chart.Main",
				"Compute ranking for advices and save them in a new collection in MongoDB.",
				new Parameter[] {
			
		    new UnflaggedOption("category", JSAP.STRING_PARSER,
		    		JSAP.NO_DEFAULT, JSAP.NOT_REQUIRED, JSAP.GREEDY,
		    		"categories for which rank must be computed; " +
		    		"if left blank, it will be computed for all."),
			
			new FlaggedOption("alpha", JSAP.DOUBLE_PARSER,
					".75", JSAP.NOT_REQUIRED, 'a', "alpha",
					"Alpha value used for KatzParallelGaussSeidel.") ,
		});
		
		JSAPResult args = jsap.parse( rawArguments );
		if ( jsap.messagePrinted() ) System.exit( 1 );
		
		
		Category[] categories;
		
		if (args.contains("category"))
			categories = Category.findAll(args.getStringArray("category"));
		else
			categories = Category.getCategories();
		
		LOGGER.info("These categories will be ranked: " + Arrays.toString(categories));
		ProgressLogger progressLogger = new ProgressLogger(LOGGER, "categories");
		progressLogger.expectedUpdates = categories.length;
		progressLogger.start();
		
		for (Category cat : categories) {
			LOGGER.info("Ranking " + cat + "...");
			
			Voting votes = new Voting(cat);
			Long2DoubleMap rank = new Ranker(votes, args.getDouble("alpha")).computeRank();
			new PercentileSaver(rank, cat).computeAndSave();
			new ItemRanker(cat).apply(rank).save().findMaxNormAndSaveIt();
			
			progressLogger.update();
			LOGGER.info("Ranking of " + cat + " has been completed.");
		}
		
		progressLogger.done();
		
		
	}

}
